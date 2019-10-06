#!/usr/bin/env python
import multiprocessing
from subprocess import call
import csv

try:
    import mapnik2 as mapnik
except:
    import mapnik

import sys, os, random as rd
import tensorflow as tf, cv2
import numpy as np
import h5py

# Define some parameters
# layers = ['complete','amenity', 'barriers','bridge','buildings','landcover','landuse','natural','others','roads','text','water']
layers = ['s2v']

save_dir = '/images'
initial_row = 0 # The first row to process
dataset_name = "routes"
num_threads = 4 
zoom_levels = [17,18,19,20]
num_items = len(zoom_levels)
size = 0.0005
hdf5_filename = save_dir + '/' + 'london_center.hdf5'

def _int64_feature(value):
    return tf.train.Feature(int64_list=tf.train.Int64List(value=[value]))
    
def _floats_feature(value):
    return tf.train.Feature(float_list=tf.train.FloatList(value=[value]))
           
def _bytes_feature(value):
  return tf.train.Feature(bytes_list=tf.train.BytesList(value=value))

def save_data(data, layers, location):
    global num_items
    global header

    ''' Data will have this structure 
    class
        Node (A numpy array with the size [item, layer, jpg_string])
    '''

    # The hdf5 filename will have 
    dt = h5py.special_dtype(vlen=np.dtype('uint8'))
    path = '/' + location['loc_id']
    with h5py.File(hdf5_filename, 'a') as f:
        dset = f.create_dataset(path, (num_items,len(layers),), dtype=dt)
        for item in range(0,num_items):
            for l, layer in enumerate(layers):
                img = data[(item, layer)]
                dset[item, l] = np.frombuffer(img, dtype='uint8')


class RenderThread:
    def __init__(self, q, printLock):
        self.q = q
        self.maxZoom = 1
        self.printLock = printLock
        self.width = 256
        self.height = 256

    def rendertiles(self, cpoint, data, item, layer, teta, zoom):
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


        #render the map to an image
        im = mapnik.Image(self.width,self.height)
        mapnik.render(m, im)
        img = im.tostring('png256')
        #img = cv2.imdecode(np.fromstring(img, dtype=np.uint8), 1)
        #img =np.asarray(img)
        data[(item, layer)]= img
        
    def loop(self):          
        while True:
            #Fetch a tile from the queue and render it
            r = self.q.get()
            if (r == None):
                self.q.task_done()
                break
            else:
                (bounds, data, item, layer, teta, zoom) = r
            self.rendertiles(bounds, data, item, layer, teta, zoom)
            self.printLock.acquire()
            self.printLock.release()
            self.q.task_done()

def render_location(locations):
    global size
    global num_items
    global num_threads
    global layers
    global initial_row

    location = locations[initial_row:len(locations)]
    for x, location in enumerate(locations):
        print('saving node {}/{}'.format(x, len(locations), end='\r'))
        lat = float(location['lat'])
        lon = float(location['lon']) 
        cpoint = [lon, lat]
        with multiprocessing.Manager() as manager:
            data = manager.dict()   # Create a list that can be shared between processes
            queue = multiprocessing.JoinableQueue(32)
            printLock = multiprocessing.Lock()
            renderers = {}
            for i in range(num_threads):
                renderer = RenderThread( queue, printLock)
                render_thread = multiprocessing.Process(target=renderer.loop)
                render_thread.start()
                #print "Started render thread %s" % render_thread.getName()
                renderers[i] = render_thread
            
            #---Generate num_tems images from shifting in the range [0,0.8*size] and rotating
            for item in range(0,len(zoom_levels)):
                shift_lat = 0 # No shift 
                shift_lon = 0 # No shift

                # Read osm_yaw and osm_yaw, if they don't match adjust
                #osm_yaw = float(location['osm_yaw'])
                gsv_yaw = float(location['gsv_yaw'])
                #if abs(osm_yaw-gsv_yaw) > 90:
                #    teta = -180 -1 * gsv_yaw
                #else:
                #    teta = -1 * gsv_yaw 
                teta = -1 * gsv_yaw
                zoom = zoom_levels[item]
                for layer in layers:
                    new_cpoint = [cpoint[0]+shift_lon, cpoint[1]+shift_lat]
                    t = (new_cpoint, data, item, layer, teta, zoom)
                    queue.put(t)
            # Signal render threads to exit by sending empty request to queue
            for i in range(num_threads):
                queue.put(None)
            # wait for pending rendering jobs to complete
            queue.join()
        
            for i in range(num_threads):
                renderers[i].join()
            save_data(data, layers, location)
            #if x == 10:
            #    break


# Open the csv with the location information
locations = []
with open('/map_data/london_new_locations_not_none.csv') as csvfile:
    reader = csv.DictReader(csvfile)
    header = reader.fieldnames
    for row in reader:
        locations.append(row)    

print("{} Pointes were found".format(len(locations)))
print(locations[0]) 

render_location(locations)
sys.stdout.flush()
