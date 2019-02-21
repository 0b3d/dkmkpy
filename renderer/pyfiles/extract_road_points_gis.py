import psycopg2, pickle

#Define function to query info, return a tuple
def query_attributes(locations):
    size = 0.0005
    line_list = []
    point_list = []
    polygon_list = []
    for location in locations:
        lat, lon = location[0], location[1]
        # , leisure, tourism, railway, water, tags
        query1 = """ SELECT name, highway
        FROM planet_osm_line
        WHERE planet_osm_line.way &&
        ST_Transform(
        ST_MakeEnvelope({}, {}, {}, {}, 
        4326),3857
        ) and name <> 'Park Row' and highway <> '';
        """
        query1 = query1.format(lon-size,lat-size,lon+size,lat+size)
        cur.execute(query1)
        res = cur.fetchall()
        line_list.append(res)
        # Query data from points
        
        query2 = """ SELECT amenity, building, religion, shop, tourism, tags
        FROM planet_osm_point
        WHERE planet_osm_point.way &&
        ST_Transform(
        ST_MakeEnvelope({}, {}, {}, {}, 
        4326),3857
        );
        """
        query2 = query2.format(lon-size,lat-size,lon+size,lat+size)
        cur.execute(query1)
        res = cur.fetchall()
        point_list.append(res)

        # Query data from polygons
        query3 = """ SELECT amenity, landuse, shop, building, sport, tags
        FROM planet_osm_polygon
        WHERE planet_osm_polygon.way &&
        ST_Transform(
        ST_MakeEnvelope({}, {}, {}, {}, 
        4326),3857
        );
        """
        query3 = query3.format(lon-size,lat-size,lon+size,lat+size)
        cur.execute(query2)
        res = cur.fetchall()
        polygon_list.append(res)
    return line_list, point_list, polygon_list

# Query the main information
conn = psycopg2.connect("dbname='gis' user='postgres' host='f978bc0bd1f8'")
cur = conn.cursor()

query = """
SELECT ST_Y((dp).geom), ST_X((dp).geom), name, highway, junction, sidewalk, lit, lanes, noexit
FROM(
    SELECT ST_DumpPoints(ST_Transform(way,4326)) AS dp, name, highway, junction, tags->'sidewalk' as sidewalk, tags->'lit' as lit, tags->'lanes' as lanes, tags->'noexit' as noexit
    FROM planet_osm_line 
    WHERE name = 'Queen's Road' and highway <> ''
    ORDER BY name
    ) As foo;

"""

cur.execute(query)
locations = cur.fetchall()

line, point, polygon = query_attributes(locations)

for location in locations:
    print(location[0:2])
for entry in line:
    print(entry)
    

# #Now query noexit points
# #query = """ SELECT ST_X(ST_Transform(way,4326)), ST_Y(ST_Transform(way,4326)) -- tags 
# #FROM  planet_osm_point
# #WHERE tags @> 'noexit=>yes'::hstore;
# #"""
# #cur.execute(query)
# #noexit = cur.fetchall()
# #for entry in noexit:
# #    print(entry)

# query_limits = """
# select min(st_xmin(st_transform(way,4326))), min(st_ymin(st_transform(way,4326))), max(st_xmax(st_transform(way,4326))), max(st_ymax(st_transform(way,4326))) from planet_osm_line where name<>'' and highway<>'';
# """
# cur.execute(query_limits)
# extreme = cur.fetchall()

# print("Minimun , Maximum :")
# print(extreme)

# #-------Save in a Pickel File -----------------------------
# #file_path = "/map_data/locations_data.pkl"
# #with open( file_path, 'wb') as f:
# #    pickle.dump(locations, f)



