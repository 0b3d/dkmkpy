import psycopg2, pickle

#Define function to query info, return a tuple
def query_properties(locations):
    lista = []
    for location in locations:
        lat, lon = location[0], location[1]
        query = """ SELECT name
        FROM planet_osm_line
        WHERE ST_Intersects(planet_osm_line.way, ST_Transform(ST_SetSRID(ST_MakePoint({}, {}),4326), 3857))
        """
        # To query info in a radio of 100 m
        query2= """ SELECT name
        FROM planet_osm_line
        WHERE ST_DWithin(planet_osm_line.way, ST_Transform(ST_SetSRID(ST_MakePoint({}, {}),4326), 3857), 100)
        """
        query = query2.format(lon, lat)
        cur.execute(query)
        res = cur.fetchall()
        print(res)
        res.insert(0, lon)
        res.insert(0, lat)
        lista.append(res)
    return lista

#Define function to query info, return a tuple
def query_attributes(locations):
    lista = []
    for location in locations:
        lat, lon = location[0], location[1]
        query = """ SELECT name, highway, junction
        FROM planet_osm_line
        WHERE planet_osm_line.way &&
        ST_Transform(
        ST_MakeEnvelope({}, {}, {}, {}, 
        4326),3857
        ) and highway <> '';
        """
        size = 0.0005
        query = query.format(lon-size,lat-size,lon+size,lat+size)
        cur.execute(query)
        res = cur.fetchall()
        res.insert(0, lon)
        res.insert(0, lat)
        lista.append(res)
    return lista


conn = psycopg2.connect("dbname='gis' user='postgres' host='f9f32644024e'")
cur = conn.cursor()

#Load pickle file
pickle_file = "/map_data/locations_p2.pkl"
with open(pickle_file, 'rb') as f:
    locations = pickle.load(f)
print("{} Pointes were found".format(len(locations)))
locations=locations[0:1000]

# Features to extract 

# To be classes
#   highway from planet_osm_line (residential, primary, ...)
#   highway from planet_osm_point (bus_stop, traffic_lights, crossing)
#   junction from planet_osm_line (roundabout)
road_properties = query_properties(locations)
print("{} points were found".format(len(road_properties)))
for loc_properties in road_properties:
    #if loc_properties[0][0]!= None:
    print(loc_properties)

# To be attributes
#   water from planet_osm_line
#   railway from planet_osm_line
#   leisure from planet_osm_line
#   tourism from planet_osm_point & planet_osm_line
#   religius from planet_osm_point
#   shop from planet_osm_point
#   building from planet_osm_point
#   amenity from planet_osm_point and planet_osm_polygon
#   landuse from planet_osm_polygon (forest, grass, military)
#   shop from planet_osm_polygon
#   building from planet_osm_polygon
#   sport from planet_osm_polygon





# Extract name of street and highway type
# lista = []
# for location in locations:
#     lat, lon = location[0], location[1]
#     query = """ SELECT public_transport
#     FROM planet_osm_line
#     WHERE planet_osm_line.way &&
#     ST_Transform(
#     ST_MakeEnvelope({}, {}, {}, {}, 
#     4326),3857
#     );
#     """
#     size = 0.0005
#     query = query.format(lon-size,lat-size,lon+size,lat+size)
#     cur.execute(query)
#     res = cur.fetchall()
#     lista.append(res)

