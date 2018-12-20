import psycopg2, pickle

conn = psycopg2.connect("dbname='gis' user='postgres' host='898211930dc6'")
cur = conn.cursor()

query = """
SELECT name, ST_asText((dp).geom) As wknode
FROM(
    SELECT name, ST_DumpPoints(ST_Transform(way,4326)) AS dp 
    FROM planet_osm_line 
    WHERE name <> '' and highway <> ''
    ORDER BY name
    ) As foo;

"""

cur.execute(query)
nodes = cur.fetchall()

for i in range(0,len(nodes)):
    print(nodes[i])
print("{} points were found".format(len(nodes)))

query2 = """
select min(st_xmin(st_transform(way,4326))), min(st_ymin(st_transform(way,4326))), max(st_xmax(st_transform(way,4326))), max(st_ymax(st_transform(way,4326))) from planet_osm_line where name<>'' and highway<>'';
"""
cur.execute(query2)
extreme = cur.fetchall()

print("Minimun , Maximum :")
print(extreme)

#-------Save in a Pickel File -----------------------------
file_path = "/map_data/road_nodes.pkl"
with open( file_path, 'wb') as f:
    pickle.dump(nodes, f)



