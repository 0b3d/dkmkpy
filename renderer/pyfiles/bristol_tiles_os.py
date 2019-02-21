#!/usr/bin/env python

try:
    import mapnik2 as mapnik
except:
    import mapnik

import sys, os
from StringIO import StringIO
import tensorflow as tf, cv2 , pickle, numpy as np, random as rd

# Set up projections
# spherical mercator (most common target map projection of osm data imported with osm2pgsql)
merc = mapnik.Projection('+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over')

# long/lat in degrees, aka ESPG:4326 and "WGS 84" 
longlat = mapnik.Projection('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')
# can also be constructed as:
#longlat = mapnik.Projection('+init=epsg:4326')


def _int64_feature(value):
    return tf.train.Feature(int64_list=tf.train.Int64List(value=[value]))
    
def _floats_feature(value):
    return tf.train.Feature(float_list=tf.train.FloatList(value=[value]))
           
def _bytes_feature(value):
  return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))

def save_data(data, layers, item, label, lat, lon, writer):
    
    coordinates = str(lat) + ',' + str(lon)
    feature = { 
            'label': _int64_feature(label),
            'coordinates' : _bytes_feature(coordinates),
            'lat'  : _floats_feature(lat),
            'lon'  : _floats_feature(lon),
            'item' : _int64_feature(item)
           }
    for i in range(len(layers)): 
        feature[layers[i]]= _bytes_feature(tf.compat.as_bytes(data[i]))
    # Create an example protocol buffer
    example = tf.train.Example(features=tf.train.Features(feature=feature))
    
    # Serialize to string and write on the file
    writer.write(example.SerializeToString())

# ensure minimum mapnik version
if not hasattr(mapnik,'mapnik_version') and not mapnik.mapnik_version() >= 600:
    raise SystemExit('This script requires Mapnik >=0.6.0)')

def rendertiles( bounds, item, label, lat, layers, lon, projec, writer):
    z = 1
    imgx = 128 * z
    imgy = 128 * z
    
    for layer in layers:
        index = layers.index(layer)
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
        
        if index == 0:
            data=[img]
            #data = np.expand_dims(data, 0) 
        else:            
            data.append(img)    
                    
    save_data(data, layers, item, label, lat, lon, writer)

def render_location(label, layers, location, size, writer):
    lon = float(location[1].split('(')[1].split(')')[0].split()[0])
    lat = float(location[1].split('(')[1].split(')')[0].split()[1])
        
    cpoint = [lon, lat]
    
    #---Generate 21 images from shifting in the range [0,0.8*size] and rotating
    for item in range(0 , 21) :
        if item == 0:
            shift_lat = 0
            shift_lon = 0
            teta = 0
        else:    
            shift_lat = 0.8*size*(rd.random()-rd.random()) 
            shift_lon = 0.8*size*(rd.random()-rd.random()) 
            teta = 360*rd.random()
        new_cpoint = [cpoint[0]+shift_lon, cpoint[1]+shift_lat]
        bounds = (new_cpoint[0]-size, new_cpoint[1]+size, new_cpoint[0]+size, new_cpoint[1]-size ) 
        aeqd = mapnik.Projection('+proj=aeqd +ellps=WGS84 +lat_0=90 +lon_0='+str(teta))
        rendertiles(bounds, item, label, lat, layers, lon, aeqd, writer)
    
def render_locations(layers, locations, size, writer):

    if not os.path.isdir(save_dir):
        print("Directory no exists, exit...")
        exit()     
    ntiles = 0
    label = 0
    total_locations = len(locations)
    total_tiles = 21 * total_locations * len(layers)
    for location in locations:
        ntiles+= 21*12
        label += 1
        print("Rendering location " + str(label) + "/" + str(total_locations))
        render_location(label, layers, location, size, writer)
        print("Images rendered and saved: " + str(ntiles) + "/" + str(total_tiles))
    print("Job done ...")

if __name__ == "__main__":
    layers = ['complete','amenity', 'barriers','bridge','buildings','landcover','landuse','natural','others','roads','text','water']
    size = 0.0005
    road_nodes = "/map_data/road_nodes.pkl"
    save_dir = "/images/roads_tfrecords/" 
    
    datasets = ["train", "validation", "test"]
    process = {"train": True, "validation": False, "test": False}
    porcentages = [[0,0.0001], [0.02,0.03], [0.03,0.0301]] #in %  
    
    with open(road_nodes, 'rb') as f:
        locations = pickle.load(f)
    print("{} Pointes were found".format(len(locations)))

    # Divide the dataset and render
    for dataset in datasets:
        if process[dataset] == True:
            print("Creating tfrecords for {} dataset encoding with cv2 and tf".format(dataset))
            filename = save_dir + '/' + dataset + '_locations.tfrecords'
            dataset_init = int(porcentages[datasets.index(dataset)][0]*len(locations))
            dataset_fin  = int(porcentages[datasets.index(dataset)][1]*len(locations))
            locations_to_render = locations[dataset_init:dataset_fin]
            print("Num of locations to render: " + str(len(locations_to_render)))
            print("Num of tiles to render: " + str(len(locations_to_render)* len(layers) * 21))
            writer = tf.python_io.TFRecordWriter(filename)
            render_locations(layers, locations_to_render, size, writer)
            writer.close()
            sys.stdout.flush()
        else:
            print("Nothin to process for the dataset " + dataset)
            

                

            
    

