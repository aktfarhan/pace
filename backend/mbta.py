"""The MBTA V3 API client every live fetch goes through, and the alert it returns."""

import os
import sys
from typing import Any, TypedDict

import httpx
from dotenv import load_dotenv

# Reads the .env
load_dotenv()

API_KEY = os.environ["MBTA_API_KEY"]
BASE_URL = "https://api-v3.mbta.com"

# Longest an MBTA call may run before it is dropped
MBTA_TIMEOUT = 5.0


class InformedEntity(TypedDict, total=False):
    """One thing an alert names."""

    route: str
    route_type: int
    direction_id: int
    stop: str
    trip: str
    facility: str


class ActivePeriod(TypedDict):
    """When an alert is in effect."""

    start: str
    end: str | None


class AlertAttributes(TypedDict):
    """What an alert says."""

    effect: str
    cause: str
    severity: int
    header: str
    service_effect: str
    lifecycle: str
    updated_at: str
    active_period: list[ActivePeriod]
    informed_entity: list[InformedEntity]


class Alert(TypedDict):
    """One alert from the feed."""

    id: str
    attributes: AlertAttributes


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
