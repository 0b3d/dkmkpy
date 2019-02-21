import psycopg2, pickle

def query_road_points_list():
    # Query the main information
    conn = psycopg2.connect("dbname='gis' user='postgres' host='f978bc0bd1f8'")
    cur = conn.cursor()
    query = """
    SELECT ST_Y((dp).geom), ST_X((dp).geom), name, highway, junction, sidewalk, lit, lanes, noexit
    FROM(
        SELECT ST_DumpPoints(ST_Transform(way,4326)) AS dp, name, highway, junction, tags->'sidewalk' as sidewalk, tags->'lit' as lit, tags->'lanes' as lanes, tags->'noexit' as noexit
        FROM planet_osm_line 
        WHERE name = 'Park Row' and highway <> ''
        ORDER BY name
    ) As foo;
    """
    cur.execute(query)
    points = cur.fetchall()
    return points 

def query_near_roads(lat, lon):
    conn = psycopg2.connect("dbname='gis' user='postgres' host='f978bc0bd1f8'")
    cur = conn.cursor()
    size = 0.001
    query = """ SELECT name
    FROM planet_osm_line
    WHERE planet_osm_line.way &&
    ST_Transform(
    ST_MakeEnvelope({}, {}, {}, {}, 
    4326),3857
    ) and name <> 'Park Row' and highway <> '';
    """
    query = query.format(lon-size,lat-size,lon+size,lat+size)
    cur.execute(query)
    near_streets = cur.fetchall()
    streets = []
    for street in near_streets:
        streets.append(street[0])            
    return streets
        
def query_intersections(street1, near_roads):
    intersections = []
    conn = psycopg2.connect("dbname='gis' user='postgres' host='f978bc0bd1f8'")
    cur = conn.cursor()
    for street2 in near_roads:
        qmark = street2.find("'")
        if qmark != None:
            street2 = street2 + 
        
        query = """
        select ST_Y(ST_Transform(the_intersection, 4326)), ST_X(ST_Transform(the_intersection, 4326))
        from
        (select distinct(ST_Intersection(b.way, a.way)) as the_intersection
        from
        (select way from planet_osm_line where name = '{}' ) as a,
        (select way from planet_osm_line where name = '{}') as b
        where a.way && b.way and ST_Intersects(b.way, a.way)
        ) as Foo;
        """
        query = query.format(street1, street2)
        print(query)
        intersection = cur.fetchall()
    return intersection

# Query the main information
locations = query_road_points_list()
for location in locations:
    street = location[2]
    lat, lon = location[0], location[1]
    near_roads = query_near_roads(lat, lon)
    intersections = query_intersections(street, near_roads)





