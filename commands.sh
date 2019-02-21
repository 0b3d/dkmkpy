sudo docker exec -it $(sudo docker ps -aqf "ancestor=dkmkpy_renderer") /bin/bash
sudo docker exec -it $(sudo docker ps -aqf "ancestor=dkmkpy_postgis") /bin/bash

mkdir -p /map_data/data
rm -r /map_data/symbols
mkdir -p /map_data/symbols
cp -f -r /openstreetmap-carto/data/* /map_data/data
cp -f -r /openstreetmap-carto/symbols/* /map_data/symbols
python /pyfiles/generate_xml_os.py /map_data/stylesheet.xml /map_data/bs_osm.xml --accept-none
#Ahora ya tengo el bs_osm.xml en /map_data
python /pyfiles/bristol_tiles.py

pkill gopnikrender
pkill gopnikdispatcher
