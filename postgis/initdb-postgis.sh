#!/bin/sh

set -e

# Perform all actions as $POSTGRES_USER
export PGUSER="$POSTGRES_USER"

# Create the 'template_postgis' template db
psql --dbname="$POSTGRES_DB" <<- 'EOSQL'
CREATE DATABASE template_postgis;
UPDATE pg_database SET datistemplate = TRUE WHERE datname = 'template_postgis';
EOSQL

# Load PostGIS into both template_database and $POSTGRES_DB
for DB in template_postgis "$POSTGRES_DB"; do
	echo "Loading PostGIS extensions into $DB"
	psql --dbname="$DB" <<-'EOSQL'
		CREATE EXTENSION postgis;
		CREATE EXTENSION postgis_topology;
		CREATE EXTENSION fuzzystrmatch;
		CREATE EXTENSION postgis_tiger_geocoder;
		CREATE EXTENSION hstore;
EOSQL
done

#import GB data to database
echo "Loading GB data to gis dataset"
osm2pgsql --style /openstreetmap-carto/openstreetmap-carto.style -d gis -U postgres -k --slim /great-britain-latest.osm.pbf

# Added ---------------------------------------------------------------------------------------------------

# Create databases
for DB in pgr_london, pgr_bristol, pgr_birmingham; do 
	# Create the 'template_postgis' template db
	psql --dbname="$DB" <<- 'EOSQL'
	CREATE DATABASE template_postgis;
	UPDATE pg_database SET datistemplate = TRUE WHERE datname = 'template_postgis';
	EOSQL

# Load PostGIS into the pgr_databases
for DB in pgr_london, pgr_bristol, pgr_birmingham; do
	echo "Loading PostGIS extensions into $DB"
	psql --dbname="$DB" <<-'EOSQL'
		CREATE EXTENSION postgis;
		CREATE EXTENSION pgrouting;
EOSQL
done

# Convert data to load in the pgr_datasets
echo "Converting pbf to osm"
osmconvert /London.osm.pbf --drop-author --drop-version --out-osm -o=/London.osm
osmconvert /Bristol.osm.pbf --drop-author --drop-version --out-osm -o=/Bristol.osm
osmconvert /Birmingham.osm.pbf --drop-author --drop-version --out-osm -o=/Birmingham.osm

echo "Loading osm to databases"
osm2pgrouting --host localhost -U postgres --password postgres --f /London.osm --dbname pgr_london
osm2pgrouting --host localhost -U postgres --password postgres --f /Bristol.osm --dbname pgr_bristol
osm2pgrouting --host localhost -U postgres --password postgres --f /Birmingham.osm --dbname pgr_birmingham
echo "Finished"

touch /var/lib/postgresql/data/DB_INITED
