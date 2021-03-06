#!/usr/bin/env python
import multiprocessing
from subprocess import call
import csv

try:
    import mapnik2 as mapnik
except:
    import mapnik

import sys, os, random as rd
import tensorflow as tf, cv2 , pickle, time
import random 
from GSV import GSV
num_loc_saved = 0



def _int64_feature(value):
    return tf.train.Feature(int64_list=tf.train.Int64List(value=[value]))
    
def _floats_feature(value):
    return tf.train.Feature(float_list=tf.train.FloatList(value=[value]))
           
def _bytes_feature(value):
  return tf.train.Feature(bytes_list=tf.train.BytesList(value=value))

def save_data(data, layers, label, tile_lat, tile_lon, num_items, pano, writer):
    pano_image, _id, pano_lat, pano_lon = pano['pano'], pano['id'], pano['pano_lat'], pano['pano_lon']
    for item in range(0,num_items):
        feature = { 
            'label': _int64_feature(label),
            'tile_lat'  : _floats_feature(tile_lat),
            'tile_lon'  : _floats_feature(tile_lon),
            'pano_lat'  : _floats_feature(pano_lat),
            'pano_lon'  : _floats_feature(pano_lon),
            'item' : _int64_feature(item),
            'pano' : _bytes_feature([pano_image]),
            'id' :   _bytes_feature([_id])  
            }
        for layer in layers: 
            feature[layer] = _bytes_feature([tf.compat.as_bytes(data[(item, layer)])])

        # Create an example protocol buffer
        example = tf.train.Example(features=tf.train.Features(feature=feature))
    
        # Serialize to string and write on the file
        writer.write(example.SerializeToString())

        location = [label,tile_lat,tile_lon,pano_lat,pano_lon,_id,item]
        with open('/images/locations_in_tfr.csv', 'a') as csvFile:
            csv_writer = csv.writer(csvFile)
            csv_writer.writerow(location)
        csvFile.close()

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
        self.width = 128
        self.height = 128

    def rendertiles(self, cpoint, data, item, label, lat, layer, lon, num_items, projec, zoom):
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
                (name, bounds, data, item, label, lat, layer, lon, num_items, projec, zoom) = r
            
            self.rendertiles(bounds, data, item, label, lat, layer, lon, num_items, projec, zoom)
            self.printLock.acquire()
            self.printLock.release()
            self.q.task_done()
            
            
def render_location(label, layers, location,num_items, num_threads, size, pano, writer):
    lat = location[0]
    lon = location[1]
    cpoint = [lon, lat] # Center for pair matching
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
        for item in range(0 , num_items) :
            if item == 0:
                shift_lat = 0
                shift_lon = 0
                teta = 0
                zoom = 19
            else:    
                shift_lat = 0.1*size*(rd.random()-rd.random()) 
                shift_lon = 0.1*size*(rd.random()-rd.random()) 
                teta = 45*(rd.random()-rd.random()) #45*rd.random()
                zoom = rd.randint(18,21)
            for layer in layers:
                new_cpoint = [cpoint[0]+shift_lon, cpoint[1]+shift_lat]
                aeqd = mapnik.Projection('+proj=aeqd +ellps=WGS84 +lat_0=90 +lon_0='+str(teta))
                t = ("Bristol", new_cpoint, data, item, label, lat, layer, lon, num_items, aeqd, zoom)
                queue.put(t)
        # Signal render threads to exit by sending empty request to queue
        for i in range(num_threads):
            queue.put(None)
        # wait for pending rendering jobs to complete
        queue.join()
    
        for i in range(num_threads):
            renderers[i].join()
        save_data(data, layers, label, lat, lon, num_items, pano, writer)
    
def render_images(layers, locations, pairs_to_render, num_items, num_threads, size, writer):
    # Check if dir exists
    if not os.path.isdir(save_dir):
        print("Directory no exists, exit...")
        exit()

    npairs = 0
    total_locations = len(locations)
    loc_iter = iter(locations) 

    while npairs < pairs_to_render:
        # Take the location and check if there are panos available, if yes take the first pano 
        start = time.time()
        positive_location = next(loc_iter)
        positive_location_GSV = GSV(positive_location[0], positive_location[1], 1) 
        while positive_location_GSV.pano_list == [None] or positive_location_GSV.pano_list == None:
            print("No GSV for this location trying with the next")
            positive_location = next(loc_iter)
            positive_location_GSV = GSV(positive_location[0], positive_location[1], 1)
        pano = {'pano':positive_location_GSV.download("list")[0], 
                'id': positive_location_GSV.pano_list_as_bytes()[0],
                'pano_lat': positive_location[0],
                'pano_lon': positive_location[1]}

        # Randomly generate a negative location, same pano different tile
        negative_index = random.randint(0,total_locations) # The idex for the negative pair
        negative_location = locations[negative_index]
        while positive_location==negative_location:
            negative_index = random.randint(0,total_locations)
            negative_location = locations[negative_index]

        # Render matched pair
        label = 1
        render_location(label, layers, positive_location, num_items, num_threads, size, pano, writer)
        # Render unmatched pair
        label = 0
        render_location(label, layers, negative_location, num_items, num_threads, size, pano, writer)
        npairs  += 2
        end = time.time()
        time_elapsed = end - start
        time_to_finish = time_elapsed * (pairs_to_render - npairs) / 3600
        print("Pairs rendered and saved: " + str(npairs) + "/" + str(pairs_to_render))
        print("Time to process a location: {} sec. Time remaining {} hours".format(time_elapsed, time_to_finish))
        print("Last location index: {}".format(locations.index(positive_location)))
    
if __name__ == "__main__":
    layers = ['complete','amenity', 'barriers','bridge','buildings','landcover','landuse','natural','others','roads','text','water']
    #layers = ['complete']   
    size = 0.0005
    # For train 
    # road_nodes = "/map_data/shuffled_road_points_bristol_manchester_cardiff_liverpool_glasgow_plymouth.pkl"
    # For evaluation
    road_nodes =  "/map_data/shuffled_road_points_london.pkl"
    save_dir = "/images/" 
    # Last porcentages of bristol render porcentages = [[0.2,0.3], [0.6,0.8], [0.8,1]] #in %  
    num_items = 1 #Total number of images by location (including rotated and shifted)

    with open('/images/locations_in_tfr.csv', 'w') as csvFile:
        csv_writer = csv.writer(csvFile)
        csv_writer.writerow(["label","tile_lat","tile_lon","pano_lat", "pano_lon","_id","item"])
        csvFile.close()
    with open(road_nodes, 'rb') as f:
        locations = pickle.load(f)
    print("{} Pointes were found".format(len(locations)))
    #rd.shuffle(locations)
    locations = locations[3698+2582:len(locations)]
    # Number of locations to form the pairs (total 669681)
    pairs_to_render = 5000

    filename = save_dir + '/train_pairs.tfrecords'
    print("Num of pairs to render: " + str(pairs_to_render))
    print("Num of tiles to render: " + str(pairs_to_render * len(layers) * num_items))
    writer = tf.python_io.TFRecordWriter(filename)
    render_images(layers, locations, pairs_to_render,num_items, NUM_THREADS, size, writer)
    writer.close()
    sys.stdout.flush()
    

                


