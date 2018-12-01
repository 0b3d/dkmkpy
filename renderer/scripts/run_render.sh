#!/usr/bin/env bash
pkill gopnikrender
pkill gopnikdispatcher
pkill gopnikslave
cp /map_data/stylesheet.xml /openstreetmap-carto

cd /gopnik/bin

./gopnikrender --config /map_data/config.json &
./gopnikdispatcher --config /map_data/config.json

pkill gopnikrender
