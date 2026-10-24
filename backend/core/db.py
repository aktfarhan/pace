"""Open connections to the Pace database."""

import os
import threading
from collections.abc import Generator
from contextlib import contextmanager

import psycopg
from dotenv import load_dotenv
from psycopg_pool import ConnectionPool

# Reads the .env
load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]

# OpenAI text-embedding-3-small
EMBEDDING_DIM = 1536

# Connections the server keeps open
POOL_MIN = 1
POOL_MAX = 4

# Seconds a request waits for a free connection
POOL_TIMEOUT = 10.0

# The server's pool
_pool: ConnectionPool | None = None
_pool_lock = threading.Lock()


def connect() -> psycopg.Connection:
    """Opens a connection of its own.

    Returns:
        An open psycopg connection read from DATABASE_URL.
    """
    return psycopg.connect(DATABASE_URL)


def pool() -> ConnectionPool:
    """Opens the server's connection pool once.

    Returns:
        The shared pool.
    """
    global _pool
    with _pool_lock:
        if _pool is None:
            _pool = ConnectionPool(
                DATABASE_URL,
                min_size=POOL_MIN,
                max_size=POOL_MAX,
                timeout=POOL_TIMEOUT,
                check=ConnectionPool.check_connection,
                open=True,
            )
        return _pool


@contextmanager
def borrow() -> Generator[psycopg.Connection, None, None]:
    """Lends a pooled connection, committing on success.

    Yields:
        A checked, open connection.
    """
    with pool().connection() as connection:
        yield connection


def close_pool() -> None:
    """Closes the server's pool."""
    global _pool
    with _pool_lock:
        if _pool is not None:
            _pool.close()
            _pool = None
