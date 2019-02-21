import pickle, random as rd
import csv

locations_data = 'renderer/map_data/locations_data.pkl'
with open(locations_data, 'rb') as f:
    locations = pickle.load(f, encoding='latin1')
print("{} Pointes were found".format(len(locations)))
locations = locations[0:1000]
rd.shuffle(locations)

for location in locations:
    print(location)