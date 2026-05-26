"""Create the chunks table and pgvector extension in Postgres."""

import os

import psycopg
from dotenv import load_dotenv

# Reads the .env
load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]

# OpenAI text-embedding-3-small
EMBEDDING_DIM = 1536

# pgvector extension and chunks table.
CREATE_EXTENSION = "CREATE EXTENSION IF NOT EXISTS vector;"

CREATE_CHUNKS = f"""
    CREATE TABLE IF NOT EXISTS chunks (
        id        text PRIMARY KEY,
        kind      text NOT NULL,
        text      text NOT NULL,
        metadata  jsonb NOT NULL,
        embedding vector({EMBEDDING_DIM})
    );
"""


def connect() -> psycopg.Connection:
    """Opens a connection to the Pace database.

    Returns:
        An open psycopg connection read from DATABASE_URL.
    """
    return psycopg.connect(DATABASE_URL)


def ensure_schema(connection: psycopg.Connection) -> None:
    """Creates the pgvector extension and chunks table if they are absent.

    Args:
        connection: An open psycopg connection.
    """
    with connection.cursor() as cursor:
        cursor.execute(CREATE_EXTENSION)
        cursor.execute(CREATE_CHUNKS)
    connection.commit()


if __name__ == "__main__":
    with connect() as connection:
        ensure_schema(connection)
    print("Schema ready: chunks table + vector extension")
