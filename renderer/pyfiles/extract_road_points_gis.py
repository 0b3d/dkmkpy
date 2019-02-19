import psycopg2, pickle

#Define function to query info, return a tuple
def query_attributes(locations):
    size = 0.0005
    line_list = []
    point_list = []
    polygon_list = []
    for location in locations:
        lon, lat = location[0], location[1]
        query1 = """ SELECT highway, leisure, tourism, railway, water, tags
        FROM planet_osm_line
        WHERE planet_osm_line.way &&
        ST_Transform(
        ST_MakeEnvelope({}, {}, {}, {}, 
        4326),3857
        );
        """
        query1 = query1.format(lon-size,lat-size,lon+size,lat+size)
        cur.execute(query1)
        res = cur.fetchall()
        line_list.append(res)
        # Query data from points
        
        query2 = """ SELECT amenity, building, religion, shop, tourism
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
        query3 = """ SELECT amenity, landuse, shop, building, sport
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
conn = psycopg2.connect("dbname='gis' user='postgres' host='f9f32644024e'")
cur = conn.cursor()

query = """
SELECT ST_X((dp).geom), ST_Y((dp).geom), ST_AsText((dp).geom) As wknode, name, highway, junction, tags
FROM(
    SELECT name, highway, junction, tags, ST_DumpPoints(ST_Transform(way,4326)) AS dp 
    FROM planet_osm_line 
    WHERE name <> '' and highway <> ''
    ORDER BY name
    ) As foo;

"""

cur.execute(query)
nodes = cur.fetchall()

# for i in range(0,len(nodes)):
#     print(nodes[i][0])
# print("{} points were found".format(len(nodes)))

# Query using tags 
#query = """ SELECT ST_X(ST_Transform(way,4326)), ST_Y(ST_Transform(way,4326)), ST_AsText(ST_Transform(way,4326)) AS pt_lonlattext -- tags 
#FROM  planet_osm_line
#WHERE tags @> 'oneway=>yes'::hstore;
#"""
# # Query using tags 
# query = """ SELECT tags 
# FROM  planet_osm_line
# WHERE highway='primary';
# """

#cur.execute(query)
#sushi = cur.fetchall()
#print(sushi)
# # Add attributes
locations = nodes[1000:1100]
line_attributes, point_attributes, polygon_attributes = query_attributes(locations)
print("Len line_atrr: ", len(line_attributes))
#print("Len point_atrr: ", len(point_attributes))
# #print("Len polygon_atrr: ", len(polygon_attributes))

for i in range(len(line_attributes)):
    print(locations[i][1], locations[i][0])
    print(line_attributes[i])
    print("\n")
#     #print(point_attributes[i])
#     #print(polygon_attributes[i])


# query2 = """
# select min(st_xmin(st_transform(way,4326))), min(st_ymin(st_transform(way,4326))), max(st_xmax(st_transform(way,4326))), max(st_ymax(st_transform(way,4326))) from planet_osm_line where name<>'' and highway<>'';
# """
# cur.execute(query2)
# extreme = cur.fetchall()

# print("Minimun , Maximum :")
# print(extreme)

# #-------Save in a Pickel File -----------------------------
# file_path = "/map_data/road_nodes.pkl"
# with open( file_path, 'wb') as f:
#     pickle.dump(nodes, f)



