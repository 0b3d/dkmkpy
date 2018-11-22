#!/usr/bin/env bash

# Compiling carto css style and generates OSM xml
# that can be passed to mapnik.

carto /openstreetmap-carto/project.mml > /map_data/stylesheet_.xml

DS='<Parameter name=\"dbname\"><![CDATA[gis]]><\/Parameter>\
    <Parameter name=\"host\"><![CDATA[postgis]]><\/Parameter>\
    <Parameter name=\"port\"><![CDATA[5432]]><\/Parameter>\
    <Parameter name=\"user\"><![CDATA[postgres]]><\/Parameter>\
    <Parameter name=\"password\"><![CDATA[postgres]]><\/Parameter>'
sed "s/<Parameter name=\"dbname\">.*<\/Parameter>/${DS}/" /map_data/stylesheet_.xml > /map_data/stylesheet.xml
rm /map_data/stylesheet_.xml

mkdir -p /map_data/data
rm -r /map_data/symbols
mkdir -p /map_data/symbols
cp -f -r /openstreetmap-carto/data/* /map_data/data
cp -f -r /openstreetmap-carto/symbols/* /map_data/symbols
#Genera el bs_osm file
python /pyfiles/generate_xml_os.py /map_data/stylesheet.xml /map_data/bs_osm.xml --accept-none
#Ahora generar una prueba 
python /pyfiles/generate_image_os.py
