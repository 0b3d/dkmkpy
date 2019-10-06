#!/usr/bin/env python
import multiprocessing
from subprocess import call

try:
    import mapnik2 as mapnik
except:
    import mapnik

import sys, os, random as rd
NUM_THREADS = 8
ntiles = 0
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
    def __init__(self, tile_dir, mapfile, q, printLock):
        self.tile_dir = tile_dir
        self.q = q
        self.mapfile = mapfile
        self.maxZoom = 1
        self.printLock = printLock
        self.width = 256
        self.height = 256
        
    def renter_tile_with_zoom(self, cpoint, data, item, label, lat, layer, lon, num_items, projec, zoom):
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

    def rendertile(self,bounds, mapfile, lon, lat, name, projec, tile_uri):
        global ntiles
        z = 1
        imgx = 128 * z
        imgy = 128 * z
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
        im.save(tile_uri,'png')      
        sys.stdout.write('output images to %s!\n' % tile_uri)
        ntiles = ntiles + 1
       
    def loop(self):
        
        self.m = mapnik.Map(128, 128)
        # Load style XML
        mapnik.load_map(self.m, self.mapfile, True)
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
                (name, bounds, mapfile, lon, lat,name, projec, tile_uri) = r

            exists= ""
            if os.path.isfile(tile_uri):
                exists= "exists"
            else:
                self.rendertile(bounds, mapfile, lon, lat, name, projec, tile_uri)
            bytes=os.stat(tile_uri)[6]
            empty= ''
            if bytes == 103:
                empty = " Empty Tile "
            self.printLock.acquire()
            print empty
            self.printLock.release()
            self.q.task_done()

def render_images(main_box,size, step, mapfile, name, num_threads):
    global ntiles
    #---------------------------------------------------
    queue = multiprocessing.JoinableQueue(32)
    printLock = multiprocessing.Lock()
    renderers = {}
    for i in range(num_threads):
        renderer = RenderThread(tile_dir, mapfile, queue, printLock)
        render_thread = multiprocessing.Process(target=renderer.loop)
        render_thread.start()
        #print "Started render thread %s" % render_thread.getName()
        renderers[i] = render_thread
        
    if not os.path.isdir(tile_dir):
        print("Directory no exists, exit...")
        exit()     
    
    lon_init = main_box[0] + size
    lon = lon_init
    i = 0
    lat_init = main_box[1] + size
    lat = lat_init
    while lon < main_box[2]:
        lon = lon_init + i * step 
        i = i + 1
        j = 0
        lat = lat_init
        while lat < main_box[3]:
            lat = lat_init + j * step        
            j = j + 1
            cpoint = [lon, lat]
            #render original image for the location
            aepd = mapnik.Projection('+proj=aeqd +ellps=WGS84 +lat_0=90 +lon_0=0')           
            bounds0 = (cpoint[0]-size, cpoint[1]+size, cpoint[0]+size, cpoint[1]-size )   
            tile_uri = tile_dir + str(lat) + '_' + str(lon) + '_' + "0" + ".png"
            # Submit tile to be rendered into the queue
            t = ("Bristol", bounds0, mapfile, lon, lat,name, aepd, tile_uri)
            queue.put(t)
            
            #---Generate 20 more images from shifting in the range [0,0.8*size]
            for k in range(1 , 21) :
                #teta = k * 45
                shift_lat = 0.8*size*(rd.random()-rd.random()) 
                shift_lon = 0.8*size*(rd.random()-rd.random()) 
                teta = 360*rd.random()
                new_cpoint = [cpoint[0]+shift_lon, cpoint[1]+shift_lat]
                bounds = (new_cpoint[0]-size, new_cpoint[1]+size, new_cpoint[0]+size, new_cpoint[1]-size ) 
                aeqd = mapnik.Projection('+proj=aeqd +ellps=WGS84 +lat_0=90 +lon_0='+str(teta))
                tile_uri = tile_dir + str(lat) + '_' + str(lon) + '_' + str(k) + ".png"
                # Submit tile to be rendered into the queue
                t = ("Bristol", bounds0, mapfile, lon, lat,name, aeqd, tile_uri)
                queue.put(t)
    
    # Signal render threads to exit by sending empty request to queue
    for i in range(num_threads):
        queue.put(None)
    # wait for pending rendering jobs to complete
    queue.join()
    for i in range(num_threads):
        renderers[i].join()
    print(str(ntiles) + " Tiles renderer")
    

if __name__ == "__main__":
    try:
        mapfile = os.environ['MAPNIK_MAP_FILE']
    except KeyError:
        mapfile = "/map_data/bs_osm.xml"
    tile_dir = "/images/ds0/" 
    step = 0.002
    size = 0.001
    main_box = (-2.714996 , 51.405203 , -2.436218, 51.537367 ) #'extent':'-325784.36424912,5743147.85822298,-253460.12347616,5714795.00655692',
    render_images(main_box,size, step, mapfile, "Bristol", NUM_THREADS)
            

