"""The OpenAI client every call shares."""

from functools import lru_cache

import httpx
from dotenv import load_dotenv
from openai import OpenAI

# Reads the .env
load_dotenv()

# Longest one read might stall before the call is dropped
LLM_TIMEOUT = httpx.Timeout(20.0, connect=5.0)

# Attempts after the first
LLM_RETRIES = 1


@lru_cache(maxsize=1)
def llm() -> OpenAI:
    """Returns the shared client, built on first use.

    Returns:
        One client, so every call reuses the same connection.
    """
    return OpenAI(timeout=LLM_TIMEOUT, max_retries=LLM_RETRIES)
