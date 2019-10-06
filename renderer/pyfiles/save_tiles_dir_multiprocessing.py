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
basic_zoom = 18
save_dir = '/images/tiles_34_eval'
tiles_by_file = 10000
initial_row = 0 # The first row to process
dataset_name = "eval_london"
num_threads = 8 
num_items = 10

class RenderThread:
    def __init__(self, save_dir, q, printLock):
        self.save_dir = save_dir
        self.q = q 
        self.printLock = printLock
        self.width = 256 
        self.height = 256 

    def render_tile(self, location, cpoint, projec, zoom, tile_uri):
        lat, lon = cpoint[0], cpoint[1]

        # target projection
        #merc = mapnik.Projection('+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over')
        merc = projec
        # WGS lat/long source projection of centre
        longlat = mapnik.Projection('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')
        
        # make a new Map object for the given mapfile
        m = mapnik.Map(self.width, self.height)
        mapfile = "/map_data/styles/bs_complete.xml"
        mapnik.load_map(m, mapfile)
        
        # ensure the target map projection is mercator
        m.srs = merc.params()
        
        # transform the centre point into the target coord sys
        centre = mapnik.Coord(lon, lat)  
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
                (location, cpoint, projec, zoom, tile_uri) = r

            exists = ''
            if os.path.isfile(tile_uri):
                exists = "exists"
            else:
                self.render_tile(location, cpoint, projec, zoom, tile_uri)

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

def render_locations(locations, num_threads, num_items, save_dir):
    queue = multiprocessing.JoinableQueue(32)
    printLock = multiprocessing.Lock()
    renderers = {}
    for i in range(num_threads):
        renderer = RenderThread(save_dir, queue, printLock)
        render_thread = multiprocessing.Process(target=renderer.loop)
        render_thread.start()
        renderers[i] = render_thread

    for location in locations:
        lat = float(location['lat'])
        lon = float(location['lon'])

        for item in range(num_items):
            if item == 0:
                shift_lat = 0
                shift_lon = 0
                teta = 0
                zoom = 18
            else:    
                shift_lat = 0.1*0.0005*(rd.random()-rd.random()) 
                shift_lon = 0.1*0.0005*(rd.random()-rd.random()) 
                teta = 360*(rd.random()-rd.random()) #45*rd.random()
                zoom = rd.randint(19,20)
            cpoint = [lat+shift_lat, lon+shift_lon]
            aeqd = mapnik.Projection('+proj=aeqd +ellps=WGS84 +lat_0=90 +lon_0='+str(teta))
            tile_uri = save_dir + '/' + location['subclass'] + '/' + location['id'] + '_' + str(item) + '.png'
            t = (location, cpoint, aeqd, zoom, tile_uri)
            queue.put(t)

    # Signal render threads to exit by sending empty request to queue
    for i in range(num_threads):
        queue.put(None)
    # wait for pending rendering jobs to complete
    queue.join()

    for i in range(num_threads):
        renderers[i].join()

# Open the csv with the location information
locations = []
with open('/map_data/tiles34_london_eval_all_points_and_classes.csv') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        locations.append(row)    

print("{} Pointes were found".format(len(locations)))
print(locations[0])

# Save the header for the csv file of resume
header = ['id','class','subclass','metaclass','lat', 'lon','city']
with open('/images/'+ dataset_name + '_' + 'resumen.csv', 'w') as csvFile:
    csv_writer = csv.writer(csvFile)
    csv_writer.writerow(header)
    csvFile.close()

# Directories
# Extract all posible classes and create a directory for each one
classes = []
subclasses = []
for location in locations:
    classes.append(location['class'])
    subclasses.append(location['subclass'])
classes = set(classes)
subclasses = set(subclasses)

# create directory tree
if not os.path.isdir(save_dir):
    os.mkdir(save_dir)

# Create a directory for each class (in this case we will take subclasses as the main classes) 
for subclass in subclasses:
    path = os.path.join(save_dir, subclass)
    if not os.path.isdir(path):
        os.mkdir(path)

render_locations(locations, num_threads, num_items, save_dir)