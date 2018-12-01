#!/usr/bin/env python

try:
    import mapnik2 as mapnik
except:
    import mapnik

import sys, os
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

def renderimage(bounds, mapfile, lon, lat, name, projec):
    z = 1
    imgx = 256 * z
    imgy = 256 * z
    map_uri = "/images/" + str(lon) + '.' + str(lat) + '_' + name + ".png"

    m = mapnik.Map(imgx,imgy)
    mapnik.load_map(m,mapfile)
    # ensure the target map projection is mercator
    m.srs = projec.params()
	
    if hasattr(mapnik,'Box2d'):
        bbox = mapnik.Box2d(*bounds)
    else:
        bbox = mapnik.Envelope(*bounds)

    # Our bounds above are in long/lat, but our map
    # is in spherical mercator, so we need to transform
    # the bounding box to mercator to properly position
    # the Map when we call `zoom_to_box()`
    transform = mapnik.ProjTransform(longlat,projec)
    merc_bbox = transform.forward(bbox)
    
    # Mapnik internally will fix the aspect ratio of the bounding box
    # to match the aspect ratio of the target image width and height
    # This behavior is controlled by setting the `m.aspect_fix_mode`
    # and defaults to GROW_BBOX, but you can also change it to alter
    # the target image size by setting aspect_fix_mode to GROW_CANVAS
    #m.aspect_fix_mode = mapnik.GROW_CANVAS
    # Note: aspect_fix_mode is only available in Mapnik >= 0.6.0
    m.zoom_to_box(merc_bbox)
    
    # render the map to an image
    im = mapnik.Image(imgx,imgy)
    mapnik.render(m, im)
    im.save(map_uri,'png')      
    # Note: instead of creating an image, rendering to it, and then 
    # saving, we can also do this in one step like:
    # mapnik.render_to_file(m, map_uri,'png')
    
    # And in Mapnik >= 0.7.0 you can also use `render_to_file()` to output
    # to Cairo supported formats if you have Mapnik built with Cairo support
    # For example, to render to pdf or svg do:
    # mapnik.render_to_file(m, "image.pdf")
    #mapnik.render_to_file(m, "image.svg")
    sys.stdout.write('output images to %s!\n' % map_uri)
    
def render_images(cpoint,shift,mapfile,lon,lat):
    #---------------------------------------------------
    # Original Image and 4 shifted
    #cpoint = [-2.603100,51.456073]     
    #cpoint = [-2.925299, 51.336877]
    cpoint1 = [cpoint[0]+shift, cpoint[1]] #x+ shifted image
    cpoint2 = [cpoint[0]-shift, cpoint[1]] #x- shifted image
    cpoint3 = [cpoint[0], cpoint[1] + shift] #y+ shifted image
    cpoint4 = [cpoint[0], cpoint[1] - shift] #y- shifted image
    bounds0 = (cpoint[0]-size, cpoint[1]+size, cpoint[0]+size, cpoint[1]-size )     # Normal image bounds
    bounds1 = (cpoint1[0]-size, cpoint1[1]+size, cpoint1[0]+size, cpoint1[1]-size ) # x+ shifted image
    bounds2 = (cpoint2[0]-size, cpoint2[1]+size, cpoint2[0]+size, cpoint2[1]-size ) # x- shifted image
    bounds3 = (cpoint3[0]-size, cpoint3[1]+size, cpoint3[0]+size, cpoint3[1]-size ) # y+ shifted image
    bounds4 = (cpoint4[0]-size, cpoint4[1]+size, cpoint4[0]+size, cpoint4[1]-size ) # y- shifted image
    
    #---------------------------------------------------
    renderimage(bounds0, mapfile, lon, lat,"0", merc)
    renderimage(bounds1, mapfile, lon, lat,"1", merc)
    renderimage(bounds2, mapfile, lon, lat,"2", merc)
    renderimage(bounds3, mapfile, lon, lat,"3", merc)
    renderimage(bounds4, mapfile, lon, lat,"4", merc)
  
    # To rotate the o rotate the map to any angle (including south up!!) and the text is rendered correctly! You don't have to change the projections of your input vectors. 
    # Simply tweak the mapnik generate_image.py script like this:
    # merc = mapnik.Projection('+proj=tpeqd +lat_1=35 +lat_2=35 +lon_1=-80 +lon_2=-122 +x_0=0 +y_0=0 +ellps=WGS84 +units=m +no_defs')
    # Rotated images 45, 90 , 135, 180, 225, 270
    for k in range(1 , 7) :
        teta = k * 45
        mercrot = mapnik.Projection('+proj=aeqd +ellps=WGS84 +lat_0=90 +lon_0='+str(teta))
        print('+proj=aeqd +ellps=WGS84 +lat_0=90 +lon_0='+str(teta))
        renderimage(bounds0, mapfile,lon, lat,str(4+k), mercrot)
    
if __name__ == "__main__":
    try:
        mapfile = os.environ['MAPNIK_MAP_FILE']
    except KeyError:
        mapfile = "/map_data/bs_osm.xml"
    
    shift = 0.0005
    step = 0.07
    size = 0.001
    #Bristol
    #main_box = (-2.925299 , 51.336877 , -2.276272, 51.591575 ) #'extent':'-325784.36424912,5743147.85822298,-253460.12347616,5714795.00655692',
    main_box = (-2.714996 , 51.405203 , -2.436218, 51.537367 ) #'extent':'-325784.36424912,5743147.85822298,-253460.12347616,5714795.00655692',
    delta_lon = main_box[2]-main_box[0]
    delta_lat = main_box[3]-main_box[1]
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
        print(i)
        while lat < main_box[3]:
            lat = lat_init + j * step        
            j = j + 1
            cpoint = [lon, lat]
            print(cpoint)
            render_images(cpoint,shift,mapfile,lon,lat)
            
            
    

