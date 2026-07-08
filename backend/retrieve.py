"""Retrieve the most similar chunks to a query from the chunks table."""

import sys
from typing import Any

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


def retrieve(query: str, k: int = 5) -> list[Row]:
    """Returns the k chunks most similar to the query.

    Args:
        query: The user's question.
        k: How many chunks to return.

    Returns:
        The top-k rows (id, kind, text, metadata, distance), closest first.
    """
    client = OpenAI()
    query_vector = Vector(embed_query(client, query))

    # Connect and pass Python lists as vectors
    connection = connect()
    register_vector(connection)

    with connection.cursor() as cursor:
        cursor.execute(SEARCH, (query_vector, k))
        return cursor.fetchall()


if __name__ == "__main__":
    query = sys.argv[1]
    for chunk_id, kind, text, metadata, distance in retrieve(query):
        print(f"{distance:.3f} {chunk_id} {text[:80]}")
