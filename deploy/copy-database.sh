#!/bin/sh
# Copies the local database into Supabase
set -eu
cd "$(dirname "$0")/.."

# LIVE_DATABASE_URL comes from the .env
set -a
. ./.env
set +a
: "${LIVE_DATABASE_URL:?Add LIVE_DATABASE_URL (the Supabase session pooler string) to .env}"

# The pace-db container has pg_dump, pg_restore and psql
local_psql() { docker exec -i pace-db psql -U pace -d pace -v ON_ERROR_STOP=1 "$@"; }
live_psql() { docker exec -i -e LIVE="$LIVE_DATABASE_URL" pace-db sh -c 'psql "$LIVE" -v ON_ERROR_STOP=1 "$@"' sh "$@"; }

# The temporary copy goes when the script ends, even when it fails
trap 'docker exec pace-db rm -f /tmp/pace.dump /tmp/pace.list' EXIT
trap 'exit 1' INT TERM

# Never over a live site's saved places
saved=0
if [ -n "$(live_psql -tAc "SELECT to_regclass('public.saved_places');")" ]; then
    saved=$(live_psql -tAc "SELECT count(*) FROM saved_places;")
fi
if [ "$saved" != "0" ]; then
    echo "Supabase already holds $saved saved places; stopping so they aren't replaced."
    exit 1
fi

echo "Dumping the local database"
docker exec pace-db pg_dump -U pace -d pace -Fc --no-owner --no-privileges -f /tmp/pace.dump

# Left out: extensions (made below), chunks (copied apart), an unread index, and saved data
docker exec pace-db sh -c 'pg_restore -l /tmp/pace.dump | grep -v -e " EXTENSION " -e "TABLE DATA public chunks " -e "CONSTRAINT public address_points address_points_pkey " -e "TABLE DATA public readings " -e "TABLE DATA public saved_places " -e "TABLE DATA public saved_trips " -e "SEQUENCE SET public saved_" > /tmp/pace.list'

echo "Making the extensions"
live_psql -c "CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;" -c "CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;"
schemas=$(live_psql -tAc "SELECT string_agg(extname || '=' || extnamespace::regnamespace, ' ' ORDER BY extname) FROM pg_extension WHERE extname IN ('pg_trgm', 'vector');")
if [ "$schemas" != "pg_trgm=public vector=public" ]; then
    echo "The extensions must be in the public schema, but Supabase has: $schemas"
    echo "Disable vector and pg_trgm under Database > Extensions, then run this again."
    exit 1
fi

echo "Restoring into Supabase (a few minutes)"
docker exec -e LIVE="$LIVE_DATABASE_URL" pace-db sh -c 'pg_restore -L /tmp/pace.list --clean --if-exists --no-owner --no-privileges --exit-on-error -d "$LIVE" /tmp/pace.dump'

echo "Copying chunks without the bus-stop embeddings"
live_psql -c "TRUNCATE chunks;"
local_psql -c "COPY (SELECT id, kind, text, metadata, CASE WHEN kind = 'stop' AND metadata->>'location_type' = '0' THEN NULL ELSE embedding END FROM chunks) TO STDOUT;" \
    | live_psql -c "COPY chunks FROM STDIN;"

# Supabase's public API can't read or write these tables
live_psql -tAc "SELECT format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY;', tablename) FROM pg_tables WHERE schemaname = 'public';" \
    | live_psql -q
live_psql -q -c "ANALYZE chunks, towns, streets, address_points, places;"

echo "Done. Local and Supabase row counts, then Supabase's size:"
for table in chunks towns streets address_points places; do
    echo "  $table: $(local_psql -tAc "SELECT count(*) FROM $table;") local, $(live_psql -tAc "SELECT count(*) FROM $table;") Supabase"
done
echo "  chunks with embeddings: $(local_psql -tAc "SELECT count(embedding) FROM chunks;") local, $(live_psql -tAc "SELECT count(embedding) FROM chunks;") Supabase"
echo "  database size: $(live_psql -tAc "SELECT pg_size_pretty(pg_database_size(current_database()));")"
