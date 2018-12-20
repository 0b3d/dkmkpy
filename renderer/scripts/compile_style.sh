#!/usr/bin/env bash

# Compiling carto css style and generates OSM xml
# that can be passed to mapnik.

cp -f -r /map_data/mml/* /openstreetmap-carto
carto /openstreetmap-carto/project.mml > /map_data/styles/complete_.xml
carto /openstreetmap-carto/amenity.mml > /map_data/styles/amenity_.xml
carto /openstreetmap-carto/barriers.mml > /map_data/styles/barriers_.xml
carto /openstreetmap-carto/bridge.mml > /map_data/styles/bridge_.xml
carto /openstreetmap-carto/buildings.mml > /map_data/styles/buildings_.xml
carto /openstreetmap-carto/landcover.mml > /map_data/styles/landcover_.xml
carto /openstreetmap-carto/landuse.mml > /map_data/styles/landuse_.xml
carto /openstreetmap-carto/natural.mml > /map_data/styles/natural_.xml
carto /openstreetmap-carto/others.mml > /map_data/styles/others_.xml
carto /openstreetmap-carto/roads.mml > /map_data/styles/roads_.xml
carto /openstreetmap-carto/text.mml > /map_data/styles/text_.xml
carto /openstreetmap-carto/water.mml > /map_data/styles/water_.xml


DS='<Parameter name=\"dbname\"><![CDATA[gis]]><\/Parameter>\
    <Parameter name=\"host\"><![CDATA[postgis]]><\/Parameter>\
    <Parameter name=\"port\"><![CDATA[5432]]><\/Parameter>\
    <Parameter name=\"user\"><![CDATA[postgres]]><\/Parameter>\
    <Parameter name=\"password\"><![CDATA[postgres]]><\/Parameter>'
sed "s/<Parameter name=\"dbname\">.*<\/Parameter>/${DS}/" /map_data/styles/complete_.xml > /map_data/styles/complete.xml
rm /map_data/styles/complete_.xml

DS='<Parameter name=\"dbname\"><![CDATA[gis]]><\/Parameter>\
    <Parameter name=\"host\"><![CDATA[postgis]]><\/Parameter>\
    <Parameter name=\"port\"><![CDATA[5432]]><\/Parameter>\
    <Parameter name=\"user\"><![CDATA[postgres]]><\/Parameter>\
    <Parameter name=\"password\"><![CDATA[postgres]]><\/Parameter>'
sed "s/<Parameter name=\"dbname\">.*<\/Parameter>/${DS}/" /map_data/styles/amenity_.xml > /map_data/styles/amenity.xml
rm /map_data/styles/amenity_.xml

DS='<Parameter name=\"dbname\"><![CDATA[gis]]><\/Parameter>\
    <Parameter name=\"host\"><![CDATA[postgis]]><\/Parameter>\
    <Parameter name=\"port\"><![CDATA[5432]]><\/Parameter>\
    <Parameter name=\"user\"><![CDATA[postgres]]><\/Parameter>\
    <Parameter name=\"password\"><![CDATA[postgres]]><\/Parameter>'
sed "s/<Parameter name=\"dbname\">.*<\/Parameter>/${DS}/" /map_data/styles/barriers_.xml > /map_data/styles/barriers.xml
rm /map_data/styles/barriers_.xml


DS='<Parameter name=\"dbname\"><![CDATA[gis]]><\/Parameter>\
    <Parameter name=\"host\"><![CDATA[postgis]]><\/Parameter>\
    <Parameter name=\"port\"><![CDATA[5432]]><\/Parameter>\
    <Parameter name=\"user\"><![CDATA[postgres]]><\/Parameter>\
    <Parameter name=\"password\"><![CDATA[postgres]]><\/Parameter>'
sed "s/<Parameter name=\"dbname\">.*<\/Parameter>/${DS}/" /map_data/styles/bridge_.xml > /map_data/styles/bridge.xml
rm /map_data/styles/bridge_.xml

DS='<Parameter name=\"dbname\"><![CDATA[gis]]><\/Parameter>\
    <Parameter name=\"host\"><![CDATA[postgis]]><\/Parameter>\
    <Parameter name=\"port\"><![CDATA[5432]]><\/Parameter>\
    <Parameter name=\"user\"><![CDATA[postgres]]><\/Parameter>\
    <Parameter name=\"password\"><![CDATA[postgres]]><\/Parameter>'
sed "s/<Parameter name=\"dbname\">.*<\/Parameter>/${DS}/" /map_data/styles/buildings_.xml > /map_data/styles/buildings.xml
rm /map_data/styles/buildings_.xml

DS='<Parameter name=\"dbname\"><![CDATA[gis]]><\/Parameter>\
    <Parameter name=\"host\"><![CDATA[postgis]]><\/Parameter>\
    <Parameter name=\"port\"><![CDATA[5432]]><\/Parameter>\
    <Parameter name=\"user\"><![CDATA[postgres]]><\/Parameter>\
    <Parameter name=\"password\"><![CDATA[postgres]]><\/Parameter>'
sed "s/<Parameter name=\"dbname\">.*<\/Parameter>/${DS}/" /map_data/styles/landcover_.xml > /map_data/styles/landcover.xml
rm /map_data/styles/landcover_.xml


DS='<Parameter name=\"dbname\"><![CDATA[gis]]><\/Parameter>\
    <Parameter name=\"host\"><![CDATA[postgis]]><\/Parameter>\
    <Parameter name=\"port\"><![CDATA[5432]]><\/Parameter>\
    <Parameter name=\"user\"><![CDATA[postgres]]><\/Parameter>\
    <Parameter name=\"password\"><![CDATA[postgres]]><\/Parameter>'
sed "s/<Parameter name=\"dbname\">.*<\/Parameter>/${DS}/" /map_data/styles/landuse_.xml > /map_data/styles/landuse.xml
rm /map_data/styles/landuse_.xml


DS='<Parameter name=\"dbname\"><![CDATA[gis]]><\/Parameter>\
    <Parameter name=\"host\"><![CDATA[postgis]]><\/Parameter>\
    <Parameter name=\"port\"><![CDATA[5432]]><\/Parameter>\
    <Parameter name=\"user\"><![CDATA[postgres]]><\/Parameter>\
    <Parameter name=\"password\"><![CDATA[postgres]]><\/Parameter>'
sed "s/<Parameter name=\"dbname\">.*<\/Parameter>/${DS}/" /map_data/styles/natural_.xml > /map_data/styles/natural.xml
rm /map_data/styles/natural_.xml


DS='<Parameter name=\"dbname\"><![CDATA[gis]]><\/Parameter>\
    <Parameter name=\"host\"><![CDATA[postgis]]><\/Parameter>\
    <Parameter name=\"port\"><![CDATA[5432]]><\/Parameter>\
    <Parameter name=\"user\"><![CDATA[postgres]]><\/Parameter>\
    <Parameter name=\"password\"><![CDATA[postgres]]><\/Parameter>'
sed "s/<Parameter name=\"dbname\">.*<\/Parameter>/${DS}/" /map_data/styles/others_.xml > /map_data/styles/others.xml
rm /map_data/styles/others_.xml


DS='<Parameter name=\"dbname\"><![CDATA[gis]]><\/Parameter>\
    <Parameter name=\"host\"><![CDATA[postgis]]><\/Parameter>\
    <Parameter name=\"port\"><![CDATA[5432]]><\/Parameter>\
    <Parameter name=\"user\"><![CDATA[postgres]]><\/Parameter>\
    <Parameter name=\"password\"><![CDATA[postgres]]><\/Parameter>'
sed "s/<Parameter name=\"dbname\">.*<\/Parameter>/${DS}/" /map_data/styles/roads_.xml > /map_data/styles/roads.xml
rm /map_data/styles/roads_.xml


DS='<Parameter name=\"dbname\"><![CDATA[gis]]><\/Parameter>\
    <Parameter name=\"host\"><![CDATA[postgis]]><\/Parameter>\
    <Parameter name=\"port\"><![CDATA[5432]]><\/Parameter>\
    <Parameter name=\"user\"><![CDATA[postgres]]><\/Parameter>\
    <Parameter name=\"password\"><![CDATA[postgres]]><\/Parameter>'
sed "s/<Parameter name=\"dbname\">.*<\/Parameter>/${DS}/" /map_data/styles/text_.xml > /map_data/styles/text.xml
rm /map_data/styles/text_.xml

DS='<Parameter name=\"dbname\"><![CDATA[gis]]><\/Parameter>\
    <Parameter name=\"host\"><![CDATA[postgis]]><\/Parameter>\
    <Parameter name=\"port\"><![CDATA[5432]]><\/Parameter>\
    <Parameter name=\"user\"><![CDATA[postgres]]><\/Parameter>\
    <Parameter name=\"password\"><![CDATA[postgres]]><\/Parameter>'
sed "s/<Parameter name=\"dbname\">.*<\/Parameter>/${DS}/" /map_data/styles/water_.xml > /map_data/styles/water.xml
rm /map_data/styles/water_.xml

mkdir -p /map_data/styles/data
rm -r /map_data/styles/symbols
mkdir -p /map_data/styles/symbols
cp -f -r /openstreetmap-carto/data/* /map_data/styles/data
cp -f -r /openstreetmap-carto/symbols/* /map_data/styles/symbols
#Generate maps
python /pyfiles/generate_xml_os.py /map_data/styles/complete.xml /map_data/styles/bs_complete.xml --accept-none
python /pyfiles/generate_xml_os.py /map_data/styles/amenity.xml /map_data/styles/bs_amenity.xml --accept-none
python /pyfiles/generate_xml_os.py /map_data/styles/barriers.xml /map_data/styles/bs_barriers.xml --accept-none
python /pyfiles/generate_xml_os.py /map_data/styles/bridge.xml /map_data/styles/bs_bridge.xml --accept-none
python /pyfiles/generate_xml_os.py /map_data/styles/buildings.xml /map_data/styles/bs_buildings.xml --accept-none
python /pyfiles/generate_xml_os.py /map_data/styles/landcover.xml /map_data/styles/bs_landcover.xml --accept-none
python /pyfiles/generate_xml_os.py /map_data/styles/landuse.xml /map_data/styles/bs_landuse.xml --accept-none
python /pyfiles/generate_xml_os.py /map_data/styles/natural.xml /map_data/styles/bs_natural.xml --accept-none
python /pyfiles/generate_xml_os.py /map_data/styles/others.xml /map_data/styles/bs_others.xml --accept-none
python /pyfiles/generate_xml_os.py /map_data/styles/roads.xml /map_data/styles/bs_roads.xml --accept-none
python /pyfiles/generate_xml_os.py /map_data/styles/text.xml /map_data/styles/bs_text.xml --accept-none
python /pyfiles/generate_xml_os.py /map_data/styles/water.xml /map_data/styles/bs_water.xml --accept-none


#Ahora generar una prueba 
python /pyfiles/generate_image_os.py
