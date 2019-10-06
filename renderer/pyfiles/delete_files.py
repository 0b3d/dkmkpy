import os, sys 
import csv

with open('/map_data/files_to_delete_22.csv') as csvfile:
    reader = csv.DictReader(csvfile)
    count = 0
    for row in reader:
        for i in range(10):
            filename = '/images/50x1500/22/' + row['id'] + '_' + str(i)
            os.remove(filename)
            count += 1
            print("Files removed: ", count)