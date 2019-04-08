import psycopg2, pickle, numpy as np
import sys, os, cv2, math, random
import xml.etree.ElementTree as ET
from renderer.Renderer import render_location_multiprocessing
from pyproj import Proj, transform
try:
    import mapnik2 as mapnik
except:
    import mapnik

try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen

class Location():
    
    def __init__(self, X, Y, epsg):
        # Data is a list containing infor asociated with each point 
        # [lat, lon, name, highway, juntion, sidewalk, lit, lanes, noexit]
        def create_cursor():
            db = "dbname='gis' user='postgres' host='{}'"
            db = db.format(self.host)
            conn = psycopg2.connect(db)
            cur = conn.cursor()
            return cur
        
        def transform_proj(X, Y):
            inProj = Proj(init='epsg:3857')
            outProj = Proj(init='epsg:4326')
            lat, lon = transform(inProj,outProj,X,Y)
            return lat, lon

        def transform_to_3857(X, Y):
            inProj = Proj(init='epsg:4326')
            outProj = Proj(init='epsg:3857')
            lat, lon = transform(inProj,outProj,X,Y)
            return lon, lat

        def get_pano_list(xml_url):
            pano_id_list = []
            response = urlopen(xml_url)
            tree = ET.parse(response)  
            root =tree.getroot()
            data_properties = root.find('data_properties')
            if data_properties == None:
                pano_id_list.append(None)
            else:
                pano_id = data_properties.get('pano_id')
                pano_id_list.append(pano_id)
                for prop in root.findall('annotation_properties'):
                    if prop != []:
                        for link in prop.findall('link'):
                            pano_id = link.get('pano_id')
                            pano_id_list.append(pano_id)
            return pano_id_list
        
        if epsg == 3857:
            self.X = X
            self.Y = Y
            self.lon, self.lat = transform_proj(self.X,self.Y)
        else:
            self.lat = X
            self.lon = Y
            self.X, self.Y = transform_to_3857(self.lat,self.lon)

        self.host = "localhost"
        self.size = 0.0005
        self.width = 128
        self.height = 128
        self.cursor = create_cursor()
        self.mapfile = "renderer/map_data/styles/bs_complete.xml"
        self.pano_zoom = 1
        self.xml_url = 'http://maps.google.com/cbk?output=xml&ll=' + str(self.lat) + ',' + str(self.lon)
        self.pano_list = get_pano_list(self.xml_url)

    def __str__(self):
        message = """
        Point: {},{} 
        """
        message = message.format(self.lat, self.lon)
        return message
    
    def pano_list_as_bytes(self):
        if self.pano_list != [None]:
            id_list = []
            for pano_id in self.pano_list:
                id_list.append(pano_id.encode('utf-8'))
        else:
            id_list = [None]
        return id_list

    def url_to_image(self, url):
        resp = urlopen(url)
        image = np.asarray(bytearray(resp.read()), dtype="uint8")
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        return image
    
    def concatenate_pano_tiles(self, pano_id):
        x_range = [0,1]
        y_range = [0]
        pano = np.zeros((512*len(y_range), 512*len(x_range), 3), dtype= 'uint8')
        for x in x_range:
            for y in y_range:
                tile_url = 'http://maps.google.com/cbk?output=tile&zoom=' + str(self.pano_zoom) + '&x=' +str(x)+ '&y=' + str(y) +'&cb_client=maps_sv&fover=2&onerr=3&renderer=spherical&v=4&panoid=' + pano_id
                img = self.url_to_image(tile_url)
                pano[512*y:512*(y+1), 512*x:512*(x+1),...] = img
        return pano

    def show_panos(self, one_or_all):
        if self.pano_list != [None]:
            if one_or_all == "all":
                for pano_id in self.pano_list:
                    image = Location.concatenate_pano_tiles(self, pano_id)
                    cv2.imshow("Original",image)
                    image = cv2.resize(image, (224, 224))
                    cv2.imshow("Resized",image)
                    cv2.waitKey(0)
            else:
                pano_id = self.pano_list[0]
                image = Location.concatenate_pano_tiles(self, pano_id)
                image = cv2.resize(image, (224, 224))
                cv2.imshow("Image_window",image)
                cv2.waitKey(1)
                    
        else:
            print("Empty pano_id list")
    
    def download_panos(self, option):
        images = []
        for pano_id in self.pano_list:
            image = Location.concatenate_pano_tiles(self, pano_id)
            image = cv2.resize(image, (224, 224))
            images.append(image)
        if option == "decoded_list":
            return images
        elif option == "tensor":
            tensor = np.stack(images)
            return tensor
        elif option == "list":
            images_list = []
            for image in images:
                image_string = cv2.imencode('.jpg', image)[1].tostring()
                images_list.append(image_string)
            return images_list
    
    def show_info(self):
        print("Pano_id list: ", self.pano_list)
        print("location: lat: {}, lon: {}".format(self.lat, self.lon))

    def getXY(self, zoom):
        """
            Generates an X,Y tile coordinate based on the latitude, longitude 
            and zoom level
            Returns:    An X,Y tile coordinate
        """
        
        tile_size = 256

        # Use a left shift to get the power of 2
        # i.e. a zoom level of 2 will have 2^2 = 4 tiles
        numTiles = 1 << zoom

        # Find the x_point given the longitude
        point_x = (tile_size/ 2 + self.lon * tile_size / 360.0) * numTiles / tile_size

        # Convert the latitude to radians and take the sine
        sin_y = math.sin(self.lat * (math.pi / 180.0))

        # Calulate the y coorindate
        point_y = ((tile_size / 2) + 0.5 * math.log((1+sin_y)/(1-sin_y)) * -(tile_size / (2 * math.pi))) * numTiles / tile_size

        return point_x, point_y
    
    def render_location(self):
        # spherical mercator (most common target map projection of osm data imported with osm2pgsql)
        merc = mapnik.Projection('+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over')
        longlat = mapnik.Projection('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')
        mapfile = "renderer/map_data/styles/bs_complete.xml"
        bounds = (self.lon-self.size, self.lat-self.size, self.lon+self.size,self.lat+self.size)
        z = 1
        imgx = 224 * z
        imgy = 224 * z
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
        #render the map to an image
        im = mapnik.Image(imgx,imgy)
        mapnik.render(m, im)
        img = im.tostring('png256')
        img = cv2.imdecode(np.fromstring(img, dtype=np.uint8), 1)
        img =np.asarray(img)
        window_name = "Location"
        cv2.imshow(window_name, img)
        cv2.waitKey(0)
        #image_uri = 'image.png'
        #im.save(image_uri,'png')
        #sys.stdout.write('output image to %s!\n' % image_uri)

    def render_location_with_variants(self, variants):
               # target projection
        #merc = mapnik.Projection('+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over')
        data = []
        for item in range(0,variants):
            if item == 0:
                teta = 0
                zoom = 20
                shift_lat = 0
                shift_lon = 0
            else:
                shift_lat = 0.1*self.size*(random.random()-random.random()) 
                shift_lon = 0.1*self.size*(random.random()-random.random())
                teta = 45 * (random.random()-random.random())
                zoom = random.randint(17,21)

            layer = "complete"
            projec = mapnik.Projection('+proj=aeqd +ellps=WGS84 +lat_0=90 +lon_0='+str(teta))        
            # WGS lat/long source projection of centre
            longlat = mapnik.Projection('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')
            
            # make a new Map object for the given mapfile
            m = mapnik.Map(self.width, self.height)
            mapfile = "renderer/map_data/styles/bs_" + layer + ".xml"
            mapnik.load_map(m, mapfile)
            
            # ensure the target map projection is mercator
            m.srs = projec.params()
            
            # transform the centre point into the target coord sys
            centre = mapnik.Coord(self.lon+shift_lon, self.lat+shift_lat)  
            transform = mapnik.ProjTransform(longlat, projec)
            merc_centre = transform.forward(centre)
            
            # 360/(2**zoom) degrees = 256 px
            # so in merc 1px = (20037508.34*2) / (256 * 2**zoom)
            # hence to find the bounds of our rectangle in projected coordinates + and - half the image width worth of projected coord units
            
            dx = ((20037508.34*2*(self.width/2)))/(256*(2 ** (zoom)))
            minx = merc_centre.x - dx
            maxx = merc_centre.x + dx
            
            # grow the height bbox, as we only accurately set the width bbox
            m.aspect_fix_mode = mapnik.aspect_fix_mode.ADJUST_BBOX_HEIGHT

            bounds = mapnik.Box2d(minx, merc_centre.y-10, maxx, merc_centre.y+10) # the y bounds will be fixed by mapnik due to ADJUST_BBOX_HEIGHT
            m.zoom_to_box(bounds)

            # render the map image to a file
            # mapnik.render_to_file(m, output)
            #render the map to an image
            im = mapnik.Image(self.width,self.height)
            mapnik.render(m, im)
            img = im.tostring('png256')
            img = cv2.imdecode(np.fromstring(img, dtype=np.uint8), 1)
            img =np.asarray(img)
            data.append(img)
        data = np.stack(data)
        return data

    def render_location_multiprocessing(self, variants):
        data = render_location_multiprocessing(self.lat, self.lon, variants)
        return data
        
    def render_location_with_zoom(self, zoom):
        # target projection
        merc = mapnik.Projection('+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over')

        # WGS lat/long source projection of centrel 
        longlat = mapnik.Projection('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')
        
        # make a new Map object for the given mapfile
        m = mapnik.Map(self.width, self.height)
        mapnik.load_map(m, self.mapfile)
        
        # ensure the target map projection is mercator
        m.srs = merc.params()
        
        # transform the centre point into the target coord sys
        centre = mapnik.Coord(self.lon, self.lat)  
        transform = mapnik.ProjTransform(longlat, merc)
        merc_centre = transform.forward(centre)
        
        # 360/(2**zoom) degrees = 256 px
        # so in merc 1px = (20037508.34*2) / (256 * 2**zoom)
        # hence to find the bounds of our rectangle in projected coordinates + and - half the image width worth of projected coord units
        dx = ((20037508.34*2*(self.width/2)))/(256*(2 ** (zoom)))
        minx = merc_centre.x - dx
        maxx = merc_centre.x + dx
        
        # grow the height bbox, as we only accurately set the width bbox
        m.aspect_fix_mode = mapnik.aspect_fix_mode.ADJUST_BBOX_HEIGHT

        bounds = mapnik.Box2d(minx, merc_centre.y-10, maxx, merc_centre.y+10) # the y bounds will be fixed by mapnik due to ADJUST_BBOX_HEIGHT
        m.zoom_to_box(bounds)

        # render the map image to a file
        # mapnik.render_to_file(m, output)


        #render the map to an image
        im = mapnik.Image(self.width,self.height)
        mapnik.render(m, im)
        img = im.tostring('png256')
        img = cv2.imdecode(np.fromstring(img, dtype=np.uint8), 1)
        img =np.asarray(img)
        window_name = "Location"
        cv2.imshow(window_name, img)
        cv2.waitKey(1)

    def get_tiles_from_server(self, variants, server):
        """
            Generates an image by stitching a number of OSM tiles together.
            
            Args:
                x:        x-tile coordinate
                y:        y-tile coordinate

            Returns:
                A high-resolution OSM image.
        """
        def request_and_crop(zoom, x, y):
            _x = int(math.floor(x))
            _y = int(math.floor(y))

            x_mod = 0.5 - (x - _x)  #How does this desviates from 0.5
            y_mod = 0.5 - (y - _y) 

            if x_mod > 0:
                x_start = _x - 1 #1 tile before
                start_xpixel = int(math.floor((1-x_mod)*256))
            else:
                x_start = _x
                start_xpixel = int(math.floor(-1*x_mod*256))
            if y_mod > 0:
                y_start = _y - 1 #1 tile before
                start_ypixel = int(math.floor((1-y_mod)*256))
            else:
                y_start = _y
                start_ypixel = int(math.floor(-1*y_mod*256))

            tile = np.zeros((256*2, 256*2, 3), dtype= 'uint8')
            for x in range(2):
                for y in range(2):
                    url =  'http://localhost:8080/{}/{}/{}.png'.format(zoom, x_start + x, y_start + y)
                    resp = urlopen(url)
                    image = np.asarray(bytearray(resp.read()), dtype="uint8")
                    image = cv2.imdecode(image, cv2.IMREAD_COLOR)
                    tile[256*y:256*(y+1), 256*x:256*(x+1),...] = image
            tile = tile[start_ypixel:start_ypixel+256,start_xpixel:start_xpixel+256]
            return tile
        tiles = []
        for _ in range(variants):
            zoom = random.randint(19,21)
            x, y = self.getXY(zoom)      
            tile = request_and_crop(zoom, x, y)
            tile = cv2.resize(tile, (self.width, self.height))
            tiles.append(tile)
        tiles = np.stack(tiles)
        return tiles


