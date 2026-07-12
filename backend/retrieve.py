"""Retrieve the most similar chunks to a query from the chunks table."""

import re
import sys
from typing import Any

import psycopg
from openai import OpenAI
from dotenv import load_dotenv
from pgvector import Vector
from pgvector.psycopg import register_vector

from data.schema import EMBEDDING_DIM, connect

# Reads the .env
load_dotenv()

MODEL = "text-embedding-3-small"
SEARCH = """
    SELECT id, kind, text, metadata, embedding <=> %s AS distance
    FROM chunks
    ORDER BY distance
    LIMIT %s;
"""
STATIONS = """
    SELECT id, metadata->>'name' AS name
    FROM chunks WHERE metadata->>'location_type' = '1';
"""
ROUTES = """
    SELECT metadata->>'route_id' AS route_id,
           metadata->>'long_name' AS long_name,
           metadata->>'short_name' AS short_name
    FROM chunks WHERE kind = 'route';
"""
FETCH = """
    SELECT id, kind, text, metadata, embedding <=> %s AS distance
    FROM chunks WHERE id = ANY(%s) ORDER BY distance;
"""

# A retrieved row: (id, kind, text, metadata, distance)
Row = tuple[str, str, str, dict[str, Any], float]


def embed_query(client: OpenAI, query: str) -> list[float]:
    """Embeds one query with the same model as the chunks used.

    Args:
        client: An OpenAI client.
        query: The user's question.

    Returns:
        The query's embedding vector.
    """
    response = client.embeddings.create(
        model=MODEL, input=[query], dimensions=EMBEDDING_DIM
    )
    return response.data[0].embedding


def match_station_ids(cursor: psycopg.Cursor, query: str) -> list[str]:
    """Finds stations named in the query.

    Args:
        cursor: An open cursor on the database.
        query: The user's question.

    Returns:
        Chunk IDs of stations whose name appears in the query.
    """
    # Pull every station id and name from the chunks table
    cursor.execute(STATIONS)

    matched = []
    lowered = query.lower()
    for chunk_id, name in cursor.fetchall():
        # Split slash names so "Kendall/MIT" matches "kendall" or "mit"
        for part in name.lower().split("/"):
            # Word boundaries so "central" hits "central square" but not "centralized"
            if re.search(rf"\b{re.escape(part)}\b", lowered):
                matched.append(chunk_id)
                break
    return matched


def match_route_ids(cursor: psycopg.Cursor, query: str) -> list[str]:
    """Finds routes named in the query.

    Args:
        cursor: An open cursor on the database.
        query: The user's question.

    Returns:
        Route IDs whose long_name or short_name appears in the query.
        Slash names match by part. A trailing branch letter is dropped.
    """
    cursor.execute(ROUTES)
    matched = []
    lowered = query.lower()
    for route_id, long_name, short_name in cursor.fetchall():
        # Name phrases this route answers to
        phrases = long_name.lower().split("/")

        # Drop trailing branch letter so "green line" matches Green Line B
        first, _, last = long_name.lower().rpartition(" ")
        if first and len(last) == 1:
            phrases.append(first)

        # Bus short names ("1", "66")
        if short_name:
            phrases.append(short_name.lower())

        # Word-boundary match against the query
        for phrase in phrases:
            if re.search(rf"\b{re.escape(phrase)}\b", lowered):
                matched.append(route_id)
                break
    return matched


def retrieve(query: str, k: int = 5, resolve: bool = True) -> list[Row]:
    """Returns the k chunks most similar to the query.

    Args:
        query: The user's question.
        k: How many chunks to return.
        resolve: Whether to guarantee chunks for stations named in the
            query. Off for parking queries, where station names collide
            with street names and city names.

    Returns:
        Up to k rows (id, kind, text, metadata, distance), resolved
        stations first, then vector search fills the rest.
    """
    client = OpenAI()
    query_vector = Vector(embed_query(client, query))

    # Connect and pass Python lists as vectors
    connection = connect()
    register_vector(connection)

    with connection.cursor() as cursor:
        # Stations named in the query are fetched directly
        rows = []
        station_ids = match_station_ids(cursor, query) if resolve else []
        if station_ids:
            cursor.execute(FETCH, (query_vector, station_ids))
            rows.extend(cursor.fetchall())

        # Vector search fills the remaining slots
        cursor.execute(SEARCH, (query_vector, k))

        # Track resolved ids so vector results don't duplicate
        seen = {row[0] for row in rows}
        for row in cursor.fetchall():
            if row[0] not in seen and len(rows) < k:
                rows.append(row)
        return rows[:k]


if __name__ == "__main__":
    query = sys.argv[1]
    for chunk_id, kind, text, metadata, distance in retrieve(query):
        print(f"{distance:.3f} {chunk_id} {text[:80]}")
