"""The MBTA V3 API client every live fetch goes through."""

import os
import sys
from typing import Any

import httpx
from dotenv import load_dotenv

# Reads the .env
load_dotenv()

API_KEY = os.environ["MBTA_API_KEY"]
BASE_URL = "https://api-v3.mbta.com"

# Longest an MBTA call may run before it is dropped
MBTA_TIMEOUT = 5.0


def fetch(path: str, params: dict) -> dict[str, Any]:
    """Returns the parsed payload for one MBTA API call.

    Args:
        path: The endpoint ("/alerts", "/predictions", "/schedules").
        params: Query parameters for the call.

    Returns:
        The decoded JSON body.
    """
    response = httpx.get(
        f"{BASE_URL}{path}",
        params=params,
        headers={"X-API-Key": API_KEY},
        timeout=MBTA_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    path = sys.argv[1]
    print(len(fetch(path, {})["data"]), "records")
