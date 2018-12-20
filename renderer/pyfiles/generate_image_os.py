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

if __name__ == "__main__":
    layers = {0:'complete',1:'amenity', 2:'barriers',3:'bridge',4:'buildings',5:'landcover',6:'landuse',7:'natural',8:'others',9:'roads',10:'text',11:'water'}
    for i in range(0,12):
        try:
            mapfile = os.environ['MAPNIK_MAP_FILE']
        except KeyError:
            mapfile = "/map_data/styles/bs_"+ layers[i] + ".xml"
        
        map_uri = "/images/" + layers[i] + ".png"
       
        #---------------------------------------------------
        #  Change this to the bounding box you want
        #
        bounds = (-2.925299 , 51.336877 , -2.276272 , 51.591575) #'extent':'-325784.36424912,5743147.85822298,-253460.12347616,5714795.00655692',
        #---------------------------------------------------

        z = 10
        imgx = 500 * z
        imgy = 500 * z

        m = mapnik.Map(imgx,imgy)
        mapnik.load_map(m,mapfile)
        
        # ensure the target map projection is mercator
        m.srs = merc.params()

        if hasattr(mapnik,'Box2d'):
            bbox = mapnik.Box2d(*bounds)
        else:
            bbox = mapnik.Envelope(*bounds)

        transform = mapnik.ProjTransform(longlat,merc)
        merc_bbox = transform.forward(bbox)
        m.zoom_to_box(merc_bbox)

        # render the map to an image
        im = mapnik.Image(imgx,imgy)
        mapnik.render(m, im)
        im.save(map_uri,'png')
        
        sys.stdout.write('output image to %s!\n' % map_uri)
    

    
