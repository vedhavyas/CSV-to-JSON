#! /usr/bin/python

import ConfigParser
import subprocess
import time
import os
import sys
import os.path
import getopt
import csv
import sqlite3
import demjson
import copy

def quote_str(str):
	if len(str) == 0:
		return "''"
	if len(str) == 1:
		if str == "'":
			return "''''"
		else:
			return "'%s'" % str
	if str[0] != "'" or str[-1:] != "'":
		return "'%s'" % str.replace("'", "''")
	return str

def quote_list(l):
	return [quote_str(x) for x in l]

def quote_list_as_str(l):
	return ",".join(quote_list(l))

def csv_to_sqldb(sqldb, infilename, table_name):
	dialect = csv.Sniffer().sniff(open(infilename, "rt").readline())
	inf = csv.reader(open(infilename, "rt"), dialect)
	column_names = inf.next()
	colstr = ",".join(column_names)
	try:
		sqldb.execute("drop table %s;" % table_name)
	except:
		pass
	sqldb.execute("create table %s (%s);" % (table_name, colstr))
	for l in inf:
		sql = "insert into %s values (%s);" % (table_name, quote_list_as_str(l))
		sqldb.execute(sql)
	sqldb.commit()

def qsqldb( sqldb, sql_cmd, chart_no, chart_x_axis, chart_y_axis, chart_legend, chart_color, chart_count, sample_interval):
	"""Run a SQL command on the specified (open) sqlite3 database, and write out the output."""
	#
	# Execute SQL
	curs = sqldb.cursor()
	curs.execute(sql_cmd)
	
	datarows = curs.fetchall()
	headers = [ item[0] for item in curs.description ]
	num_col=len(headers)
	num_row=len(datarows)
        temp= {}
        data2 = [] 
        data = []
        arr = {'id':0, 'x_axis':0, 'y_axis':0, 'legend':0, 'color':0, 'graphData':0, 'num_col':0, 'groupTable':1}
	for i in range (num_col):
	  temp['column_'+str(i)]=0
        if (num_row % int(sample_interval) != 0): 
          for i in range (num_row):
             graphdata=temp.copy()
             for j in range (num_col):
               graphdata["column_"+str(j)] = float( datarows[i][j])
             data.append(graphdata)
             if ((i+1)%int(sample_interval) == 0):
                  graphdata2=temp.copy()
                  for k in range (num_col):
                     graphdata2["column_"+str(k)]= sum(item['column_'+str(k)] for item in data)
                  for x in graphdata2:
                     graphdata2[x]=float((graphdata2[x])/int(sample_interval))
                  data2.append(graphdata2)
                  data[:] = []
             elif ((i+1) == num_row):
                  rem_sam_no=len(data)
                  graphdata3=temp.copy()
                  for k in range (num_col):
                     graphdata3["column_"+str(k)]= sum(item['column_'+str(k)] for item in data)
                  for x in graphdata3:
                     graphdata3[x]=float((graphdata3[x])/int(rem_sam_no))
                  data2.append(graphdata3)
                  data[:] = []
        else:
            for i in range (num_row):
             graphdata=temp.copy()
             for j in range (num_col):
               graphdata["column_"+str(j)] = float( datarows[i][j])
             data.append(graphdata)
             if ((i+1)%int(sample_interval) == 0):
                  graphdata2=temp.copy()
                  for k in range (num_col):
                     graphdata2["column_"+str(k)]= sum(item['column_'+str(k)] for item in data)
                  for x in graphdata2:
                     graphdata2[x]=float((graphdata2[x])/int(sample_interval))
                  data2.append(graphdata2)
                  data[:] = []
      
        temp_arr=arr.copy()
        temp_arr["id"]=chart_no
        temp_arr["x_axis"]=chart_x_axis
        temp_arr["y_axis"]=chart_y_axis
        temp_arr["legend"]=chart_legend
        temp_arr["color"]=chart_color
        temp_arr["num_col"]=num_col  
        temp_arr["graphData"]=data2
        print len(data2)
        return temp_arr


def qcsv(infilenames,file_db, keep_db, sql_cmd, chart_no, chart_x_axis, chart_y_axis, chart_legendlist, chart_color, chart_count, sample_interval):
	"""Query the listed CSV files, optionally writing the output to a sqlite file on disk."""
	#
	# Create a sqlite file, if specified   
	if file_db:
		try:
			os.unlink(file_db)
		except:
			pass
		conn = sqlite3.connect(file_db)
	else:
		conn = sqlite3.connect(":memory:")
	#
	# Move data from input CSV files into sqlite
	for csvfile in infilenames:
		inhead, intail = os.path.split(csvfile)
		tablename = os.path.splitext(intail)[0]
		csv_to_sqldb(conn, csvfile, tablename)
	#
	# Execute the SQL
	val=qsqldb( conn, sql_cmd, chart_no, chart_x_axis, chart_y_axis, chart_legendlist, chart_color, chart_count, sample_interval)
	#
	# Clean up.
	conn.close()
	if file_db and not keep_db:
		try:
			os.unlink(file_db)
		except:
			pass
        return val

if __name__=='__main__':
        config = ConfigParser.ConfigParser()
        config.read('CONF.ini')

        chart_count=int(config.get('CHART', 'chart_count'))
        table_names=[]
        chart_columnlist=[]
        chart_legendlist=[]
        finaldata = []
        for i in range (1,chart_count+1): 
           chart_name=config.get('CHART', "chart_name_"+str(i)).strip('"')
           temp=config.get('CHART', "tables_"+str(i)).strip('"')
           table_names=temp.split('|')
           table_no=len(table_names)
           chart_x_axis=config.get('CHART', "chart_x_axis_"+str(i)).strip('"')
           chart_y_axis=config.get('CHART', "chart_y_axis_"+str(i)).strip('"')
           chart_color=config.get('COLOR', "color").strip('"')
           chart_color=chart_color.split('|')
           temp1=config.get('CHART', "chart_column_list_"+str(i)).strip('"')
           chart_columnlist=temp1.split('|')
           temp2=config.get('CHART', "chart_legend_list_"+str(i)).strip('"')
           chart_legendlist=temp2.split('|')
           sample_interval=config.get('CHART', "sample_interval_"+str(i))  
           #del chart_legendlist[0]
           query_string = "SELECT " + ",".join(chart_columnlist)
           query_string = query_string + " FROM " + " and ".join(table_names)
           query_string = query_string + ';'
           outfile="final.json"
           file_db = None
           keep_db = False
           count=0
           while (count < table_no):
              table_names[count] = table_names[count] + ".csv"
              count = count + 1
           temp_data=qcsv(table_names, file_db, keep_db, query_string, i, chart_x_axis, chart_y_axis, chart_legendlist, chart_color, chart_count, sample_interval)
           print ("chart :" + str(i))
           finaldata.append(temp_data)
        json=demjson.encode(finaldata)
        finalfile=open(outfile,"wb")
        finalfile.write(json)
        finalfile.close   
