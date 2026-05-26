"""Embed chunks and load them into the chunks table."""

import json
from pathlib import Path

from openai import OpenAI
from dotenv import load_dotenv
from psycopg.types.json import Jsonb
from pgvector.psycopg import register_vector

from data.chunk_types import Chunk
from data.schema import EMBEDDING_DIM, connect, ensure_schema

# Reads the .env
load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
CHUNKS = ROOT / "data" / "chunks"
MODEL = "text-embedding-3-small"
BATCH_SIZE = 200

INSERT_CHUNK = """
    INSERT INTO chunks (id, kind, text, metadata, embedding)
    VALUES (%s, %s, %s, %s, %s);
"""


def chunk_kind(chunk_id: str) -> str:
    """Returns a chunk's kind from its id prefix.

    Args:
        chunk_id: A chunk id like "route:Red" or "stop:7954".

    Returns:
        The prefix before the colon ("route" or "stop").
    """
    return chunk_id.split(":", 1)[0]


def load_chunks() -> list[Chunk]:
    """Loads every route and stop chunk from data/chunks/.

    Returns:
        The combined chunks from routes.jsonl and stops.jsonl.
    """
    chunks: list[Chunk] = []
    for name in ("routes.jsonl", "stops.jsonl"):
        for line in (CHUNKS / name).read_text(encoding="utf-8").splitlines():
            chunks.append(json.loads(line))
    return chunks


def embed_texts(client: OpenAI, texts: list[str]) -> list[list[float]]:
    """Embeds texts in batches with text-embedding-3-small.

    Args:
        client: An OpenAI client.
        texts: The chunk texts to embed, in order.

    Returns:
        One embedding vector per input text, in the same order.
    """
    embeddings: list[list[float]] = []
    for start in range(0, len(texts), BATCH_SIZE):
        batch = texts[start : start + BATCH_SIZE]
        response = client.embeddings.create(
            model=MODEL, input=batch, dimensions=EMBEDDING_DIM
        )
        embeddings.extend(item.embedding for item in response.data)
        print(f"  embedded {len(embeddings)}/{len(texts)}")
    return embeddings


def to_row(
    chunk: Chunk, embedding: list[float]
) -> tuple[str, str, str, Jsonb, list[float]]:
    """Builds an insert row from a chunk and its embedding.

    Args:
        chunk: A loaded chunk.
        embedding: The chunk's embedding vector.

    Returns:
        A tuple of (id, kind, text, metadata, embedding) for INSERT_CHUNK.
    """
    return (
        chunk["id"],
        chunk_kind(chunk["id"]),
        chunk["text"],
        Jsonb(chunk["metadata"]),
        embedding,
    )


chunks = load_chunks()

# Connect and ensure the table exists
connection = connect()
ensure_schema(connection)
register_vector(connection)

print(f"Embedding {len(chunks)} chunks with {MODEL}")
client = OpenAI()
embeddings = embed_texts(client, [chunk["text"] for chunk in chunks])

# Rebuild the table from the current chunks
rows = [to_row(chunk, embedding) for chunk, embedding in zip(chunks, embeddings)]
with connection.cursor() as cursor:
    cursor.execute("TRUNCATE chunks")
    cursor.executemany(INSERT_CHUNK, rows)
connection.commit()

print(f"Loaded {len(chunks)} chunks into the chunks table")
