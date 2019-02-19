#!/usr/bin/env python

try:
    import mapnik2 as mapnik
except:
    import mapnik
    
import sys, os, psycopg2

connection = psycopg2.connect(database="gis",user="postgres", password="mypw", host="f9f32644024e")
cur = connection.cursor()


cur.execute("SELECT bridge FROM planet_osm_line WHERE name='Whiteladies Road' and * NOT IN (name)='' ORDER BY name;")
#cur.execute("SELECT tags FROM planet_osm_line WHERE name='Whiteladies Road' ORDER BY name;")


#cur.execute("SELECT * FROM planet_osm_roads WHERE tags @> 'highway=>residential'::hstore ORDER BY tags;")

#print(cur.fetchone())
#print(cur.fetchone())



rows = cur.fetchall()
print "\nShow me the databases:\n"
for row in rows:
	print "   ", row[0]
