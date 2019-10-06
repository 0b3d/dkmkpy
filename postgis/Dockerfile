FROM mdillon/postgis:9.5

WORKDIR /

RUN apt-get update && \
    apt-get install -y osm2pgsql osm2pgrouting osmctools git wget
#RUN apt-get update
RUN apt-get install -y postgresql-9.5-pgrouting
RUN rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/dooman87/openstreetmap-carto.git && \
    wget https://download.bbbike.org/osm/bbbike/Bristol/Bristol.osm.pbf && \
    wget https://download.bbbike.org/osm/bbbike/Birmingham/Birmingham.osm.pbf && \
    wget https://download.geofabrik.de/europe/great-britain-latest.osm.pbf && \
    wget https://download.bbbike.org/osm/bbbike/London/London.osm.pbf 


#Overriding init script to add hstore extension that osm2pgsql requires
COPY ./initdb-postgis.sh /docker-entrypoint-initdb.d/postgis.sh
