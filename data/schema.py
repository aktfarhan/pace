"""Create the Pace tables and Postgres extensions."""

import os

import psycopg
from dotenv import load_dotenv

# Reads the .env
load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]

# OpenAI text-embedding-3-small
EMBEDDING_DIM = 1536

# Vector search for chunks, trigram search for place names
CREATE_VECTOR = "CREATE EXTENSION IF NOT EXISTS vector;"
CREATE_TRIGRAM = "CREATE EXTENSION IF NOT EXISTS pg_trgm;"

CREATE_CHUNKS = f"""
    CREATE TABLE IF NOT EXISTS chunks (
        id        text PRIMARY KEY,
        kind      text NOT NULL,
        text      text NOT NULL,
        metadata  jsonb NOT NULL,
        embedding vector({EMBEDDING_DIM})
    );
"""

# The 351 municipalities
CREATE_TOWNS = """
    CREATE TABLE IF NOT EXISTS towns (
        id      integer PRIMARY KEY,
        name    text NOT NULL,
        display text NOT NULL,
        rta     text
    );
"""

# Street names, normalized for search; neighborhood splits duplicate names in a town
CREATE_STREETS = """
    CREATE TABLE IF NOT EXISTS streets (
        id           integer PRIMARY KEY,
        name         text NOT NULL,
        display      text NOT NULL,
        town_id      integer NOT NULL REFERENCES towns(id),
        neighborhood text,
        lat          double precision NOT NULL,
        lon          double precision NOT NULL,
        points       integer NOT NULL
    );
"""
CREATE_STREETS_INDEX = """
    CREATE INDEX IF NOT EXISTS streets_name_trgm
        ON streets USING gin (name gin_trgm_ops);
"""

# One point per house number on a street
CREATE_ADDRESS_POINTS = """
    CREATE TABLE IF NOT EXISTS address_points (
        street_id   integer NOT NULL REFERENCES streets(id),
        number_text text NOT NULL,
        number      integer NOT NULL,
        lat         double precision NOT NULL,
        lon         double precision NOT NULL,
        PRIMARY KEY (street_id, number_text)
    );
"""
CREATE_ADDRESS_POINTS_INDEX = """
    CREATE INDEX IF NOT EXISTS address_points_street
        ON address_points (street_id, number);
"""

# Stations, aliases, landmarks, and neighborhoods, searchable by name
CREATE_PLACES = """
    CREATE TABLE IF NOT EXISTS places (
        id         text PRIMARY KEY,
        kind       text NOT NULL,
        category   text,
        notable    boolean NOT NULL DEFAULT false,
        name       text NOT NULL,
        display    text NOT NULL,
        address    text,
        agency     text,
        station_id text,
        town_id    integer REFERENCES towns(id),
        lat        double precision,
        lon        double precision,
        source     text NOT NULL
    );
"""
CREATE_PLACES_INDEX = """
    CREATE INDEX IF NOT EXISTS places_name_trgm
        ON places USING gin (name gin_trgm_ops);
"""
CREATE_SAVED_PLACES = """
    CREATE TABLE IF NOT EXISTS saved_places (
        id      bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        code    text NOT NULL,
        label   text NOT NULL,
        address text NOT NULL
    );
"""
CREATE_SAVED_PLACES_INDEX = """
    CREATE INDEX IF NOT EXISTS saved_places_code
        ON saved_places (code);
"""
CREATE_SAVED_TRIPS = """
    CREATE TABLE IF NOT EXISTS saved_trips (
        id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        code        text NOT NULL,
        origin      text NOT NULL,
        destination text NOT NULL
    );
"""
CREATE_SAVED_TRIPS_INDEX = """
    CREATE INDEX IF NOT EXISTS saved_trips_code
        ON saved_trips (code);
"""


def connect() -> psycopg.Connection:
    """Opens a connection to the Pace database.

    Returns:
        An open psycopg connection read from DATABASE_URL.
    """
    return psycopg.connect(DATABASE_URL)


def ensure_schema(connection: psycopg.Connection) -> None:
    """Creates the extensions and tables if they are absent.

    Args:
        connection: An open psycopg connection.
    """
    with connection.cursor() as cursor:
        cursor.execute(CREATE_VECTOR)
        cursor.execute(CREATE_TRIGRAM)
        cursor.execute(CREATE_CHUNKS)
        cursor.execute(CREATE_TOWNS)
        cursor.execute(CREATE_STREETS)
        cursor.execute(CREATE_STREETS_INDEX)
        cursor.execute(CREATE_ADDRESS_POINTS)
        cursor.execute(CREATE_ADDRESS_POINTS_INDEX)
        cursor.execute(CREATE_PLACES)
        cursor.execute(CREATE_PLACES_INDEX)
        cursor.execute(CREATE_SAVED_PLACES)
        cursor.execute(CREATE_SAVED_PLACES_INDEX)
        cursor.execute(CREATE_SAVED_TRIPS)
        cursor.execute(CREATE_SAVED_TRIPS_INDEX)
    connection.commit()


if __name__ == "__main__":
    with connect() as connection:
        ensure_schema(connection)
    print(
        "Schema ready: chunks, towns, streets, address_points, places, "
        "saved_places, saved_trips"
    )
