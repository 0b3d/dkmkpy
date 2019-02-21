#!/usr/bin/env python
import multiprocessing
from subprocess import call

try:
    import mapnik2 as mapnik
except:
    import mapnik

import sys, os, random as rd
import tensorflow as tf, cv2 , pickle, time


def _int64_feature(value):
    return tf.train.Feature(int64_list=tf.train.Int64List(value=[value]))
    
def _floats_feature(value):
    return tf.train.Feature(float_list=tf.train.FloatList(value=[value]))
           
def _bytes_feature(value):
    return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))

def save_data(data, layers, labels, lat, lon, num_items, writer):
    
    coordinates = str(lat) + ',' + str(lon)
    for label in labels: 
        for item in range(0,num_items):
            feature = { 
                    'label': _int64_feature(label),
                    'coordinates' : _bytes_feature(coordinates),
                    'lat'  : _floats_feature(lat),
                    'lon'  : _floats_feature(lon),
                    'item' : _int64_feature(item)
                }
            feature['complete'] = _bytes_feature(tf.compat.as_bytes(data[(item, label)]))
            # Create an example protocol buffer
            example = tf.train.Example(features=tf.train.Features(feature=feature))
            # Serialize to string and write on the file
            writer.write(example.SerializeToString())

NUM_THREADS = 8
# Set up projections
# spherical mercator (most common target map projection of osm data imported with osm2pgsql)
merc = mapnik.Projection('+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over')

# long/lat in degrees, aka ESPG:4326 and "WGS 84" 
longlat = mapnik.Projection('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')
# can also be constructed as:
#longlat = mapnik.Projection('+init=epsg:4326')

# ensure minimum mapnik version
if not hasattr(mapnik,'mapnik_version') and not mapnik.mapnik_version() >= 600:
    raise SystemExit('This script requires Mapnik >=0.6.0)')


class RenderThread:
    def __init__(self, q, printLock):
        self.q = q
        self.maxZoom = 1
        self.printLock = printLock

    def rendertiles(self, bounds, data, item, label, lat, layer, lon, num_items, projec):
        z = 1
        imgx = 128 * z
        imgy = 128 * z
        
        mapfile = "/map_data/styles/bs_" + layer + ".xml"
     
        m = mapnik.Map(imgx,imgy)
        mapnik.load_map(m,mapfile)
        # ensure the target map projection is mercator
        m.srs = projec.params()
        
        if hasattr(mapnik,'Box2d'):
            bbox = mapnik.Box2d(*bounds)
        else:
            bbox = mapnik.Envelope(*bounds)

        transform = mapnik.ProjTransform(longlat,projec)
        merc_bbox = transform.forward(bbox)
        
        m.zoom_to_box(merc_bbox)
        
        # render the map to an image
        im = mapnik.Image(imgx,imgy)
        mapnik.render(m, im)
        img = im.tostring('png256')
        data[(item, label)]= img
        
    def loop(self):
        
        self.m = mapnik.Map(128, 128)
        # Load style XML
        #mapnik.load_map(self.m, self.mapfile, True)
        # Obtain <Map> projection
        self.prj = mapnik.Projection(self.m.srs)
        # Projects between tile pixel co-ordinates and LatLong (EPSG:4326)
        #self.tileproj = GoogleProjection(self.maxZoom+1)
                
        while True:
            #Fetch a tile from the queue and render it
            r = self.q.get()
            if (r == None):
                self.q.task_done()
                break
            else:
                (name, bounds, data, item, label, lat, layer, lon, num_items, projec) = r
            
            self.rendertiles(bounds, data, item, label, lat, layer, lon, num_items, projec)
            self.printLock.acquire()
            self.printLock.release()
            self.q.task_done()
            
def render_images(layers, locations, num_items, num_threads, size, writer):
    # Check if dir exists
    if not os.path.isdir(save_dir):
        print("Directory no exists, exit...")
        exit()     
    ntiles = 0
    label = 0
    total_locations = len(locations)
    total_tiles = num_items * total_locations * len(layers)
    
    #Dicidir la lista original en 10 sublistas
    delta = 1000
    num_labels = delta
    lista_maestra = [locations[x:x+delta] for x in range(0, len(locations), delta)]

    for location_batch in lista_maestra:
        queue = multiprocessing.JoinableQueue(32)
        printLock = multiprocessing.Lock()
        renderers = {}
        for i in range(num_threads):
            renderer = RenderThread( queue, printLock)
            render_thread = multiprocessing.Process(target=renderer.loop)
            render_thread.start()
            #print "Started render thread %s" % render_thread.getName()
            renderers[i] = render_thread
        with multiprocessing.Manager() as manager:
            data = manager.dict()   # Create a list that can be shared between processes
            labels = []
            start = time.time()
            for location in location_batch:
                ntiles += num_items 
                label  += 1
                labels.append(label)
                print("Rendering location " + str(label) + "/" + str(total_locations))        
                lon = float(location[1].split('(')[1].split(')')[0].split()[0])
                lat = float(location[1].split('(')[1].split(')')[0].split()[1])
                    
                cpoint = [lon, lat]
                
                #---Generate num_tems images from shifting in the range [0,0.8*size] and rotating
                for item in range(0 , num_items) :
                    if item == 0:
                        shift_lat = 0
                        shift_lon = 0
                        teta = 0
                    else:    
                        shift_lat = 0.8*size*(rd.random()-rd.random()) 
                        shift_lon = 0.8*size*(rd.random()-rd.random()) 
                        teta = 360*rd.random()
                    for layer in layers:
                        new_cpoint = [cpoint[0]+shift_lon, cpoint[1]+shift_lat]
                        bounds = (new_cpoint[0]-size, new_cpoint[1]+size, new_cpoint[0]+size, new_cpoint[1]-size ) 
                        aeqd = mapnik.Projection('+proj=aeqd +ellps=WGS84 +lat_0=90 +lon_0='+str(teta))
                        t = ("Bristol", bounds, data, item, label, lat, layer, lon, num_items, aeqd)
                        queue.put(t)
            # Signal render threads to exit by sending empty request to queue
            for i in range(num_threads):
                queue.put(None)
            # wait for pending rendering jobs to complete
        
            for i in range(num_threads):
                renderers[i].join()
            save_data(data, layers, labels, lat, lon, num_items, writer)
            end = time.time()
            time_elapsed = end - start
            time_to_finish = time_elapsed * (total_locations - label) / (delta*3600)
            print("Images rendered and saved: " + str(ntiles) + "/" + str(total_tiles))
            print("Time to process a location: {} sec. Time remaining {} hours".format(time_elapsed, time_to_finish))
    
if __name__ == "__main__":
    #layers = ['complete','amenity', 'barriers','bridge','buildings','landcover','landuse','natural','others','roads','text','water']
    layers = ['complete']   
    size = 0.0005
    road_nodes = "/map_data/road_nodes.pkl"
    save_dir = "/images/roads_tfrecords/" 
    
    datasets = ["train_rgb", "validation_rgb", "test_rgb"]
    process = {"train_rgb": True, "validation_rgb": True, "test_rgb": True}
    porcentages = [[0,0.6], [0.6,0.8], [0.8,1]] #in %  
    num_items = 10 #Total number of images by location (including rotated and shifted)
    
    with open(road_nodes, 'rb') as f:
        locations = pickle.load(f)
    print("{} Pointes were found".format(len(locations)))
    rd.shuffle(locations)

    # Divide the dataset and render
    for dataset in datasets:
        if process[dataset] == True:
            print("Creating tfrecords for {} dataset encoding with cv2 and tf".format(dataset))
            filename = save_dir + '/' + dataset + '_locations.tfrecords'
            dataset_init = int(porcentages[datasets.index(dataset)][0]*len(locations))
            dataset_fin  = int(porcentages[datasets.index(dataset)][1]*len(locations))
            locations_to_render = locations[dataset_init:dataset_fin]
            print("Num of locations to render: " + str(len(locations_to_render)))
            print("Num of tiles to render: " + str(len(locations_to_render)* len(layers) * num_items))
            writer = tf.python_io.TFRecordWriter(filename)
            render_images(layers, locations_to_render, num_items, NUM_THREADS, size, writer)
            writer.close()
            sys.stdout.flush()
        else:
            print("Nothin to process for the dataset " + dataset)
            

                


