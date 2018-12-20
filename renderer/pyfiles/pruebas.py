import pprint, pickle, sys, os, mapnik

pkl_file = open('data.pkl', 'rb')

data1 = pickle.load(data.pkl)
#pprint.pprint(data1)
im = data1[0]
im.save("/images/",'png')
#print(im)
pkl_file.close()   
