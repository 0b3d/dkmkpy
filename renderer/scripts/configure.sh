cd /map_data
mkdir -p data
cp -f -r /openstreetmap-carto/data/* /map_data/mapnik-stylesheets/data/
mkdir -p symbols
cp -f -r /openstreetmap-carto/symbols/* /map_data/mapnik-stylesheets/symbols/
mkdir -p inc2
cp -f /openstreetmap-carto/*.mss /map_data/mapnik-stylesheets/inc2

python generate_xml.py /map_data/stylesheet.xml /map_data/bs_osm.xml 
python generate_image.py
