import psycopg2, pickle
import sys, os
try:
    import mapnik2 as mapnik
except:
    import mapnik



class Bristol():

    def __init__(self, container_id):
        
        def create_cursor():
            db = "dbname='gis' user='postgres' host='{}'"
            db = db.format(self.container_id)
            conn = psycopg2.connect(db)
            cur = conn.cursor()
            return cur


        self.container_id = container_id
        self.database = "gis"
        self.cursor = create_cursor()

    def query_roads_list(self):
        query = """ SELECT DISTINCT name from planet_osm_line where name <> '' and highway <> ''
        """
        cur = self.cursor
        cur.execute(query)
        roads = cur.fetchall()
        roads_list = []
        for road in roads:
            roads_list.append(road[0])
        return roads_list

    def road_points_list(self):
        # Query the main information
        cur = self.cursor
        query = """
        SELECT ST_Y((dp).geom), ST_X((dp).geom), ST_Y((dp2).geom), ST_X((dp2).geom), name, highway, junction, sidewalk, lit, lanes, noexit
        FROM(
            SELECT ST_DumpPoints(ST_Transform(way,4326)) AS dp, ST_DumpPoints(way) AS dp2, name, highway, junction, tags->'sidewalk' as sidewalk, tags->'lit' as lit, tags->'lanes' as lanes, tags->'noexit' as noexit
            FROM planet_osm_line 
            WHERE name <> '' and highway = 'tertiary' and junction='roundabout'
            ORDER BY name
        ) As foo;
        """
        cur.execute(query)
        points = cur.fetchall()
        return points 

class Location():
    
    def __init__(self, data):
        # Data is a list containing infor asociated with each point 
        # [lat, lon, name, highway, juntion, sidewalk, lit, lanes, noexit]
        def create_cursor():
            db = "dbname='gis' user='postgres' host='{}'"
            db = db.format(self.container_id)
            conn = psycopg2.connect(db)
            cur = conn.cursor()
            return cur
    
        self.lat = data[0]
        self.lon = data[1]
        self.Y = data[2]
        self.X = data[3]
        self.name = data[4]
        self.highway = data[5]
        self.junction = data[6]
        self.sidewalk = data[7]
        self.lit = data[8]
        self.lanes = data[9]
        self.noexit = data[10]
        self.size = 0.0005
        self.container_id = '5e30668fe2a6'
        self.cursor = create_cursor()
    
    def __str__(self):
        message = """
        Point: {},{} of the road {} highway_type: {}, junction_type: {}, sidewalk: {} 
        """
        message = message.format(self.lat, self.lon, self.name, self.highway, self.junction, self.sidewalk)
        return message

    def render_location(self):
        # spherical mercator (most common target map projection of osm data imported with osm2pgsql)
        merc = mapnik.Projection('+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over')
        longlat = mapnik.Projection('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')
        mapfile = "/map_data/styles/bs_complete.xml"
        image_uri = "image.png"
        bounds = (self.lon-self.size, self.lat-self.size, self.lon+self.size,self.lat+self.size)
        z = 1
        imgx = 500 * z
        imgy = 500 * z
        m = mapnik.Map(imgx,imgy)
        mapnik.load_map(m,mapfile)
        m.srs = merc.params()
        if hasattr(mapnik,'Box2d'):
            bbox = mapnik.Box2d(*bounds)
        else:
            bbox = mapnik.Envelope(*bounds)
        transform = mapnik.ProjTransform(longlat,merc)
        merc_bbox = transform.forward(bbox)
        m.zoom_to_box(merc_bbox)
        # render the map to an image
        im = mapnik.Image(imgx,imgy)
        mapnik.render(m, im)
        im.save(image_uri,'png')
        sys.stdout.write('output image to %s!\n' % image_uri)
            
            
    def near_roads(self):
        query = """ SELECT DISTINCT name
        FROM planet_osm_line
        WHERE planet_osm_line.way &&
        ST_Transform(
        ST_MakeEnvelope({}, {}, {}, {}, 
        4326),3857
        ) and name <> 'Park Row' and highway <> '';
        """
        query = query.format(self.lon-self.size,self.lat-self.size,self.lon+self.size,self.lat+self.size)
        cur = self.cursor
        cur.execute(query)
        near_streets = cur.fetchall()
        streets = []
        for street in near_streets:
            streets.append(street[0]) # Just to remove the empty element at the end of the list            
        return streets

    def intersections(self, near_roads, point_or_box):
        cur = self.cursor
        if point_or_box == "box":
            intersections = []
            for street in near_roads:
                qmark = street.find("'") 
                if qmark != -1:
                    street = street[:qmark] + "'" + street[qmark:]          
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
                query = query.format(self.name, street)
                cur.execute(query)
                intersection = cur.fetchall()
                if intersection != None:
                    intersections.append(intersection)
            return intersections
        elif point_or_box == "point":
            for street in near_roads:
                qmark = street.find("'") 
                if qmark != -1:
                    street = street[:qmark] + "'" + street[qmark:]
                query = """
                SELECT ST_Y(foo.the_intersection), ST_X(foo.the_intersection) 
                FROM
                (SELECT ST_Intersection(ST_SetSRID(ST_MakePoint({},{}), 3857), way) as the_intersection
                FROM planet_osm_line
                WHERE name = '{}' and way &&ST_Intersection(ST_SetSRID(ST_MakePoint({},{}), 3857), way)
                ) As Foo;
                """
                query = query.format(self.X,self.Y, street,self.X,self.Y, street)
                cur.execute(query)
                intersection = cur.fetchall()
                if intersection != []:
                    intersection = 1
                else:
                    intersection = 0
                return intersection
        
    def landuse(self):
        query = """ SELECT DISTINCT landuse, water, tourism
        FROM planet_osm_polygon
        WHERE planet_osm_polygon.way &&
        ST_MakeEnvelope({}, {}, {}, {}, 
        3857)
        """
        query = query.format(self.X-self.size,self.Y-self.size,self.X+self.size,self.Y+self.size)
        query = query.format(self.X-self.size,self.Y-self.size,self.X+self.size,self.Y+self.size)
        cur = self.cursor
        cur.execute(query)
        landuse = cur.fetchall()
        landuse_list = []
        for use in landuse:
            if use != [None]:
                landuse_list.append(use[0]) # Just to remove the empty element at the end of the list            
        return landuse

bristol = Bristol("5e30668fe2a6")
locations = bristol.road_points_list()
#data = [51.4558098090449, -2.60444328242937, 6702320.72, -289925.3, 'Park Row', 'secondary', None, 'no', None, None, None]
for location in locations:
    loc = Location(location)
    print(loc)
    near_roads = loc.near_roads()
    intersections = loc.intersections(near_roads, "point")
    landuse = loc.landuse()
    print(landuse)


