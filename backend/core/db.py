"""Open connections to the Pace database."""

import os

import psycopg
from dotenv import load_dotenv

# Reads the .env
load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]

# OpenAI text-embedding-3-small
EMBEDDING_DIM = 1536


def connect() -> psycopg.Connection:
    """Opens a connection to the Pace database.

    Returns:
        An open psycopg connection read from DATABASE_URL.
    """
    return psycopg.connect(DATABASE_URL)
