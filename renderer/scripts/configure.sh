cd /map_data
mkdir -p data
cp -f -r /openstreetmap-carto/data/* /map_data/mapnik-stylesheets/data/
mkdir -p symbols
cp -f -r /openstreetmap-carto/symbols/* /map_data/mapnik-stylesheets/symbols/
mkdir -p inc2
cp -f /openstreetmap-carto/*.mss /map_data/mapnik-stylesheets/inc2

python generate_xml_os.py /map_data/stylesheet.xml /map_data/bs_osm.xml --accept-none
python generate_image.py
sudo docker exec -ti bristol-map_renderer_1_163fee586aa5 /bin/bash

