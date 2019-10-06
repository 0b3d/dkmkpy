import os, sys 
import csv, random as rd 
import tensorflow as tf
import multiprocessing
from subprocess import call
try:
    import mapnik2 as mapnik
except:
    import mapnik

# Define some parameters
zoom_levels = [19]
save_dir = '/images/edinburgh_v2'
initial_row = 0 # The first row to process
num_threads = 8 
layers = ['s2v']

class RenderThread:
    def __init__(self, save_dir, q, printLock):
        self.save_dir = save_dir
        self.q = q 
        self.printLock = printLock
        self.width = 256 
        self.height = 256 

    def render_tile(self, cpoint, tile_uri, layer, teta, zoom):
        # target projection
        merc = mapnik.Projection('+proj=aeqd +ellps=WGS84 +lat_0=90 +lon_0='+str(teta))
        #merc = mapnik.Projection('+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over')

        # WGS lat/long source projection of centrel 
        longlat = mapnik.Projection('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')
        
        # make a new Map object for the given mapfile
        m = mapnik.Map(self.width, self.height)
        #mapfile = "/map_data/styles/bs_" + layer + ".xml"
        mapfile = "/map_data/styles/" + layer + ".xml"        
        mapnik.load_map(m, mapfile)
        
        # ensure the target map projection is mercator
        m.srs = merc.params()
        
        # transform the centre point into the target coord sys
        centre = mapnik.Coord(cpoint[0], cpoint[1])  
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
        im = mapnik.Image(self.width,self.height)
        mapnik.render(m, im)
        im.save(tile_uri,'png')
        sys.stdout.write('output images to %s!\n' % tile_uri)

    def loop(self):
        while True:
            # Fetch a tile from the queue and render it
            r = self.q.get()
            if (r == None):
                self.q.task_done()
                break
            else:
                #(location, cpoint, projec, zoom, tile_uri) = r
                (new_cpoint, tile_uri, layer, teta, zoom) = r

            exists = ''
            if os.path.isfile(tile_uri):
                exists = "exists"
            else:
                self.render_tile(new_cpoint, tile_uri, layer, teta, zoom)

            bytes=os.stat(tile_uri)[6]
            empty= ''
            if bytes == 103:
                empty = " Empty Tile "
            if exists != '':
                print(exists)
            if empty != '':
                print(empty)

            self.printLock.acquire()
            self.printLock.release()
            self.q.task_done()

def render_locations(locations, num_threads, save_dir):
    # Open the csv with the location information
    queue = multiprocessing.JoinableQueue(32)
    printLock = multiprocessing.Lock()
    renderers = {}
    for i in range(num_threads):
        renderer = RenderThread(save_dir, queue, printLock)
        render_thread = multiprocessing.Process(target=renderer.loop)
        render_thread.start()
        renderers[i] = render_thread

    for i, location in enumerate(locations):
        #lat = float(row['lat'])
        #lon = float(row['lon'])
        lat = float(location[1])
        lon = float(location[2])
        cpoint = [lon, lat]

        #---Generate num_tems images from shifting in the range [0,0.8*size] and rotating
        for zoom in zoom_levels:
            shift_lat = 0 # No shift 
            shift_lon = 0 # No shift

            # Read osm_yaw and osm_yaw, if they don't match adjust
            #osm_yaw = float(location['osm_yaw'])
            gsv_yaw = float(location[3])
            #if abs(osm_yaw-gsv_yaw) > 90:
            #    teta = -180 -1 * gsv_yaw
            #else:
            #    teta = -1 * gsv_yaw 
            teta = -1 * gsv_yaw
            loc_id = location[0]
            tile_uri = os.path.join(save_dir, 'z'+str(zoom), str(loc_id)+'.png')
            for layer in layers:
                new_cpoint = [cpoint[0]+shift_lon, cpoint[1]+shift_lat]
                t = (new_cpoint, tile_uri, layer, teta, zoom)
                queue.put(t)

    # Signal render threads to exit by sending empty request to queue
    for i in range(num_threads):
        queue.put(None)
    # wait for pending rendering jobs to complete
    queue.join()

    for i in range(num_threads):
        renderers[i].join()


locations = []
with open('/map_data/locations_not_none.csv') as csvfile:
    reader = csv.DictReader(csvfile)
    for i, row in enumerate(reader):
        loc_id, lat, lon, yaw = row['loc_id'], row['gsv_lat'], row['gsv_lon'], row['gsv_yaw']
        locations.append([loc_id, lat, lon, yaw])
        #print('Reading {} line \r'.format(i))
    print("{} lines found".format(len(locations)))
render_locations(locations, num_threads, save_dir)
