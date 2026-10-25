"""Retrieve the most similar chunks to a query from the chunks table."""

import re
import sys
from functools import lru_cache
from typing import Any

import numpy as np
from openai import OpenAI
from pgvector.psycopg import register_vector

from backend.assistant.llm import SHORT_TIMEOUT, llm
from backend.core.db import EMBEDDING_DIM, borrow

MODEL = "text-embedding-3-small"

# Every chunk without the individual bus stops
SEARCHABLE = """
    SELECT id, kind, text, metadata, embedding
    FROM chunks WHERE NOT (kind = 'stop' AND metadata->>'location_type' = '0');
"""

# Lines that need prefixes
LINES = {"SL": "silver line", "CR-": "commuter rail"}

# A retrieved row: (id, kind, text, metadata, distance)
Row = tuple[str, str, str, dict[str, Any], float]


class Searchable:
    """The searchable chunks and their embeddings, held in memory."""

    def __init__(self, rows: list[tuple]):
        """Keeps the chunks and scales each embedding to length one.

        Args:
            rows: (id, kind, text, metadata, embedding) per chunk.
        """
        self.chunks = [row[:4] for row in rows]
        self.position = {chunk[0]: index for index, chunk in enumerate(self.chunks)}
        vectors = np.array([row[4].to_numpy() for row in rows], dtype=np.float32)
        self.vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)

        # Routes with the fields the matcher reads
        self.routes = [
            (meta.get("route_id"), meta.get("long_name"), meta.get("short_name"))
            for _, kind, _, meta in self.chunks
            if kind == "route"
        ]

    def distances(self, vector: list[float]) -> np.ndarray:
        """Measures the cosine distance from a query to every chunk.

        Args:
            vector: The query's embedding.

        Returns:
            One distance per chunk, in chunk order.
        """
        query = np.asarray(vector, dtype=np.float32)
        return 1.0 - self.vectors @ (query / np.linalg.norm(query))

    def row(self, index: int, distances: np.ndarray) -> Row:
        """Builds one retrieved row.

        Args:
            index: The chunk's position.
            distances: Distances from distances().

        Returns:
            (id, kind, text, metadata, distance).
        """
        return (*self.chunks[index], float(distances[index]))


@lru_cache(maxsize=1)
def searchable() -> Searchable:
    """Reads the searchable chunks once, on first use.

    Returns:
        The chunks and embeddings in memory.
    """
    with borrow() as connection:
        register_vector(connection)
        with connection.cursor() as cursor:
            cursor.execute(SEARCHABLE)
            return Searchable(cursor.fetchall())


def embed_query(client: OpenAI, query: str) -> list[float]:
    """Embeds one query with the same model as the chunks used.

    Args:
        client: An OpenAI client.
        query: The user's question.

    Returns:
        The query's embedding vector.
    """
    response = client.with_options(timeout=SHORT_TIMEOUT).embeddings.create(
        model=MODEL, input=[query], dimensions=EMBEDDING_DIM
    )
    return response.data[0].embedding


def line_of(route_id: str, long_name: str, short_name: str) -> str:
    """Reads the line a route runs under.

    Args:
        route_id: The route's id.
        long_name: Its long name.
        short_name: Its short name, or empty.

    Returns:
        The line's name, lowercased, or empty where the route has none.
    """
    # A line neither name spells out
    for prefix, line in LINES.items():
        if route_id.startswith(prefix) or short_name.startswith(prefix):
            return line

    # A line whose name ends on a branch letter
    first, _, last = long_name.lower().rpartition(" ")
    return first if first and len(last) == 1 else ""


def match_route_ids(query: str) -> list[str]:
    """Finds routes named in the query.

    Args:
        query: The user's question.

    Returns:
        Route IDs whose long_name or short_name appears in the query.
        Slash names match by part.
    """
    named = []
    by_line = []
    claimed = set()
    lowered = query.lower()
    for route_id, long_name, short_name in searchable().routes:
        # Name phrases this route answers to
        phrases = long_name.lower().split("/")

        # Bus short names ("1", "66")
        if short_name:
            phrases.append(short_name.lower())

        # The line the route runs under
        line = line_of(route_id, long_name, short_name)

        # Word-boundary match against the query
        matched = False
        for phrase in phrases:
            if re.search(rf"\b{re.escape(phrase)}\b", lowered):
                named.append(route_id)
                if line:
                    claimed.add(line)
                matched = True
                break

        # So "green line" reaches Green Line B, "silver line" reaches SL1
        if not matched and line and re.search(rf"\b{re.escape(line)}\b", lowered):
            by_line.append((route_id, line))

    # Naming one route of a line leaves the rest of it out
    for route_id, line in by_line:
        if line not in claimed:
            named.append(route_id)

    return named


def retrieve(
    query: str,
    k: int = 5,
    vector: list[float] | None = None,
    stations: list[str] | None = None,
) -> list[Row]:
    """Returns the k chunks most similar to the query.

    Args:
        query: The user's question.
        k: How many chunks to return.
        vector: The query's embedding, when it was already made.
        stations: Station ids the question's places name.

    Returns:
        Up to k rows (id, kind, text, metadata, distance), resolved
        stations first, then vector search fills the rest.
    """
    if vector is None:
        vector = embed_query(llm(), query)
    index = searchable()
    distances = index.distances(vector)

    # Stations named in the question are fetched directly
    rows = []
    for station in stations or []:
        position = index.position.get(f"stop:{station}")
        if position is not None:
            rows.append(index.row(position, distances))
    rows.sort(key=lambda row: row[4])

    # Vector search fills the rest
    nearest = np.argsort(distances, kind="stable")[:k]

    # Track resolved ids so vector results don't duplicate
    seen = {row[0] for row in rows}
    for position in nearest.tolist():
        row = index.row(position, distances)
        if row[0] not in seen and len(rows) < k:
            rows.append(row)
    return rows[:k]


if __name__ == "__main__":
    query = sys.argv[1]
    for chunk_id, kind, text, metadata, distance in retrieve(query):
        print(f"{distance:.3f} {chunk_id} {text[:80]}")
