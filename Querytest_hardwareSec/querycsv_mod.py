#!/usr/bin/python
import ConfigParser
import subprocess
import os
import sys
import csv
import os.path
import getopt
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

def qsqldb( sqldb, sql_cmd, sample_interval):
	"""Run a SQL command on the specified (open) sqlite3 database, and write out the output."""
	#
	# Execute SQL
	curs = sqldb.cursor()
	curs.execute(sql_cmd)
	
        # Fetching the graph data
	datarows = curs.fetchall()
	headers = [ item[0] for item in curs.description ]
	num_col=len(headers)
	num_row=len(datarows)
        # Declaration  of Dicts and Lists  
        temp= {}
        data = []
        # Initialization of Dicts
	for i in range (num_col+1):
	  temp['column_'+str(i)]=0
        
        # Parsing data      
        graphdata=temp.copy() 
        for i in range (num_row):
           if ((i+1)%int(sample_interval) == 0):
              for k in range (num_col):
                 graphdata["column_"+str(k+1)] += float(datarows[i][k])
              graphdata["column_0"]=str(i+1)
              for x in range (1, num_col+1):
                 graphdata["column_"+str(x)]=float((graphdata["column_"+str(x)])/int(sample_interval))
                 graphdata["column_"+str(x)]=round(graphdata["column_"+str(x)],2)  
                 graphdata["column_"+str(x)]=str(graphdata["column_"+str(x)])
              data.append(graphdata.copy())
              graphdata=temp.copy() 
           else:
              for k in range (num_col):
                 graphdata["column_"+str(k+1)] += float(datarows[i][k])
         
        
        return data


def qcsv(infilenames,file_db, keep_db, sql_cmd, sample_interval):
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
	val=qsqldb( conn, sql_cmd, sample_interval)
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

        # Reading the configuration file
        config = ConfigParser.ConfigParser()
        config.read('/var/www/html/systat_exp/CONF.ini')
        # Getting the initial data ie.. chart count 
        chart_count=int(config.get('CHART', 'chart_count'))
        table_names=[]
        chart_columnlist=[]
        chart_legendlist=[]
        finaldata = []
	hardwareData = []
        arr = {'id':0, 'x_axis':0, 'y_axis':0, 'legend':0, 'color':0, 'graphData':0, 'num_col':0, 'groupTable':1, 'chart_name':0, 'chart_unit':0, 'chart_minval':0, 'chart_maxval':0}
	arr2 = {'cpuinfo':0, 'dmidecodereport':0, 'meminfo':0, 'sysctl':0}

        # Getting the details of each chart 
        for i in range (1,chart_count+1): 
           chart_name=config.get('CHART', "chart_name_"+str(i)).strip('"')
           temp=config.get('CHART', "tables_"+str(i)).strip('"')
           table_names=temp.split('|')
           table_no=len(table_names)
           chart_name=config.get('CHART', "chart_name_"+str(i)).strip('"')
           chart_x_axis=config.get('CHART', "chart_x_axis_"+str(i)).strip('"')
           chart_y_axis=config.get('CHART', "chart_y_axis_"+str(i)).strip('"')
           chart_unit=config.get('CHART', "chart_unit_"+str(i)).strip('"')
           chart_color=config.get('COLOR', "color").strip('"')
           chart_color=chart_color.split('|')
           temp1=config.get('CHART', "chart_column_list_"+str(i)).strip('"')
           chart_columnlist=temp1.split('|')
           temp2=config.get('CHART', "chart_legend_list_"+str(i)).strip('"')
           chart_legendlist=temp2.split('|')
           sample_interval=config.get('CHART', "sample_interval_"+str(i))  
           #del chart_legendlist[0]
           chart_minval=config.get('CHART', "chart_minval_"+str(i)) 
           chart_maxval=config.get('CHART', "chart_maxval_"+str(i))
           #print chart_minval
           #print chart_maxval
           query_string = "SELECT " + ",".join(chart_columnlist)
           query_string = query_string + " FROM " + " and ".join(table_names)
           query_string = query_string + ';'
           outfile="/var/www/html/systat_exp/Graphdata.json"
	   hardwareoutfile = "/var/www/html/systat_exp/hardwareSpec.json"
           file_db = None
           keep_db = False
           count=0
           # Adding the ".csv" to each tablename
           while (count < table_no):
              table_names[count] = "/var/www/html/systat_exp/"+table_names[count] + ".csv"
              count = count + 1
           # Function qcsv is being called 
           graphData=qcsv(table_names, file_db, keep_db, query_string, sample_interval)
          
           # Writing data to dict 
           temp_arr=arr.copy()
           temp_arr["id"]=i
           temp_arr["x_axis"]=chart_x_axis
           temp_arr["y_axis"]=chart_y_axis
           temp_arr["legend"]=chart_legendlist
           temp_arr["color"]=chart_color
           temp_arr["chart_name"]=chart_name
           temp_arr["chart_unit"]=chart_unit
           temp_arr["num_col"]=len(chart_columnlist)
           temp_arr["chart_minval"]=int(chart_minval)
           temp_arr["chart_maxval"]=int(chart_maxval)
           temp_arr["graphData"]=graphData
  
           print ("chart :" + str(i) +" Data is collected")
           # Appending the collected data of each chart to a list
           finaldata.append(temp_arr)
        # Converting the final list with data of all charts into JSON format
        json=demjson.encode(finaldata)
        json="var graph_config = "+json+";"
        # Writing the json string to a File
        finalfile=open(outfile,"wb")
        finalfile.write(json)
        finalfile.close

        # Reading Hardware specification files
	hard_arr=arr2.copy()
	file = open('cpuinfo.txt', 'r')
	cpuinfo = file.read()
	file.close
	
	file = open('dmidecodereport.txt', 'r')
	dmi = file.read()
	file.close
	
	file = open('meminfo.txt', 'r')
	mem = file.read()
	file.close

	file = open('sysctl.txt', 'r')
	systcl = file.read()
	file.close

	#adding the data to dictionary
	hard_arr["cpuinfo"]=cpuinfo
	hard_arr["dmidecodereport"]=dmi
	hard_arr["meminfo"]=mem
	hard_arr["sysctl"]=systcl

	#appending data to final list
        hardwareData.append(hard_arr)
        
        #converting to json format
        hardwarejson=demjson.encode(hardwareData)
        hardwarejson="var hardware_spec = "+hardwarejson+";"
        # Writing the json string to a File
        file=open(hardwareoutfile,"wb")
        file.write(hardwarejson)
        file.close	
