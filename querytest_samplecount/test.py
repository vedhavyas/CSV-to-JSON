#!/usr/bin/python


example_list = [
    {'points': 400, 'gold': 2480},
    {'points': 100, 'gold': 610},
    {'points': 100, 'gold': 620},
    {'points': 100, 'gold': 620}
]
example= {'points':0, 'gold':0}
modified_list = []
total_gold=0
total_points=0
no=len(example_list)
example_1=example.copy()
example_1["gold"]= sum(item['gold'] for item in example_list)
example_1["points"]= sum(item['points'] for item in example_list)
example_2=example.copy()
for x in example_1:
  example_1[x]=float((example_1[x])/4) 
modified_list.append(example_1)
#i = 0
#while (i < no):
#   total_gold += example_list[i]["gold"]
#   total_points += example_list[i]["points"]
#   if (i%2 == 0):
#      temp_dict=example_dict.copy()
#      temp_dict["points"]=total_points
#      temp_dict["gold"]=total_gold
#      modified_list.append(temp_dict)
#      total_points=0
#      total_gold=0
#   if (i == no-1):
#      temp_dict=example_dict.copy()
#      temp_dict["points"]=total_points
#      temp_dict["gold"]=total_gold
#      modified_list.append(temp_dict) 
#   i += 1


#print example_list
#print modified_list
#print example_1
#print example_list
#example_list[:] = []
#print example_list

num_col=6
if (num_col%7 == 0):
  for i in range (num_col):
    print i

else:
   print "none"



