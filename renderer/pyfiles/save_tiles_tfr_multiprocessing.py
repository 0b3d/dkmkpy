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

# Define some parameters
layers = ['complete','amenity', 'barriers','bridge','buildings','landcover','landuse','natural','others','roads','text','water']
save_dir = '/images/50x1500'
tiles_by_file = 10000
initial_row = 0 # The first row to process
dataset_name = "train_1"
num_threads = 8 
num_items = 10
size = 0.0005
csv_filename = '/images/'+ dataset_name + '_' + 'resumen.csv'


def _int64_feature(value):
    return tf.train.Feature(int64_list=tf.train.Int64List(value=[value]))
    
def _floats_feature(value):
    return tf.train.Feature(float_list=tf.train.FloatList(value=[value]))
           
def _bytes_feature(value):
  return tf.train.Feature(bytes_list=tf.train.BytesList(value=value))

def save_data(data, layers, metaclass, location, writer):
    global num_items
    global csv_filename
    global header

    for item in range(0,num_items):
        features = { 
            'item' : _int64_feature(item),
            'metaclass': _int64_feature(metaclass),
            'lat'  : _floats_feature(float(location['lat'])),
            'lon'  : _floats_feature(float(location['lon'])),
            'node_id' : _int64_feature(int(location['id'])),
            'class' : _int64_feature(int(location['class'])),  
            'subclass' : _int64_feature(int(location['subclass']))
            }
        for layer in layers: 
            features[layer] = _bytes_feature([tf.compat.as_bytes(data[(item, layer)])])

        # Create an example protocol buffer
        example = tf.train.Example(features=tf.train.Features(feature=features))
    
        # Serialize to string and write on the file
        writer.write(example.SerializeToString())

        with open(filename, 'a') as csvFile:
            csv_writer = csv.DictWriter(csvFile, fieldnames = header)
            csv_writer.writerow(location)

class RenderThread:
    def __init__(self, q, printLock):
        self.q = q
        self.maxZoom = 1
        self.printLock = printLock
        self.width = 256
        self.height = 256

    def rendertiles(self, cpoint, data, item, layer, projec, zoom):
        # target projection
        #merc = mapnik.Projection('+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over')
        merc = projec
        # WGS lat/long source projection of centre
        longlat = mapnik.Projection('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')
        
        # make a new Map object for the given mapfile
        m = mapnik.Map(self.width, self.height)
        mapfile = "/map_data/styles/bs_" + layer + ".xml"
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
        data[(item, layer)]= img
        
    def loop(self):          
        while True:
            #Fetch a tile from the queue and render it
            r = self.q.get()
            if (r == None):
                self.q.task_done()
                break
            else:
                (bounds, data, item, layer, projec, zoom) = r
            self.rendertiles(bounds, data, item, layer, projec, zoom)
            self.printLock.acquire()
            self.printLock.release()
            self.q.task_done()

def render_location(locations, writer):
    global size
    global num_items
    global num_threads
    global layers
    global initial_row
    global tiles_by_file
    counter = 0

    while counter < tiles_by_file:
        index = initial_row + counter
        location = locations[index]
        metaclass = index
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
            for item in range(0 , num_items):
                if item == 0:
                    shift_lat = 0
                    shift_lon = 0
                    teta = 0
                    zoom = 18
                else:    
                    shift_lat = 0.1*size*(rd.random()-rd.random()) 
                    shift_lon = 0.1*size*(rd.random()-rd.random()) 
                    teta = 360*(rd.random()-rd.random()) #45*rd.random()
                    zoom = rd.randint(19,20)
                for layer in layers:
                    new_cpoint = [cpoint[0]+shift_lon, cpoint[1]+shift_lat]
                    aeqd = mapnik.Projection('+proj=aeqd +ellps=WGS84 +lat_0=90 +lon_0='+str(teta))
                    t = (new_cpoint, data, item, layer, aeqd, zoom)
                    queue.put(t)
            # Signal render threads to exit by sending empty request to queue
            for i in range(num_threads):
                queue.put(None)
            # wait for pending rendering jobs to complete
            queue.join()
        
            for i in range(num_threads):
                renderers[i].join()
            save_data(data, layers, metaclass, location, writer)


# Open the csv with the location information
locations = []
with open('/map_data/locations_50x1500.csv') as csvfile:
    reader = csv.DictReader(csvfile)
    header = reader.fieldnames
    for row in reader:
        locations.append(row)    

print("{} Pointes were found".format(len(locations)))
print(locations[0]) 

# Save the header for the csv file of resume
header.extend(['metaclass', 'item'])
with open(csv_filename, 'w') as csvFile:
    csv_writer = csv.DictWriter(csvFile, fieldnames=header)
    csv_writer.writeheader()

# Create the tfrecords writer 
filename = os.path.join(save_dir, dataset_name + '.tfrecords')
writer = tf.python_io.TFRecordWriter(filename)
render_location(locations, writer)
writer.close()
sys.stdout.flush()
