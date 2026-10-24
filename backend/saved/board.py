"""Plan every trip saved against a code."""

import time
from functools import lru_cache
from typing import TypedDict

from backend.assistant.cards import TripCard, trip_card
from backend.assistant.classify import ParsedQuery
from backend.assistant.retrieve import Row
from backend.core.clock import now_in_boston
from backend.planner.trip import plan_trip
from backend.reliability.risk import risk_for
from backend.saved.trips import read_trips

# Seconds one saved trip's plan is shared
PLAN_TTL = 30.0

# Saved trips whose plans are kept at once
PLANS_KEPT = 64


class Planned(TypedDict):
    """One saved trip and the plan it has right now."""

    id: int
    origin: str
    destination: str
    card: TripCard | None
    risk: str | None
    chance: float | None


def ends_only(origin: str, destination: str) -> ParsedQuery:
    """Shapes a saved trip's two ends the way the planner reads a query.

    Args:
        origin: Where the trip starts.
        destination: Where it ends.

    Returns:
        A parsed query carrying the two ends.
    """
    return {
        "intent": "route",
        "origin": origin,
        "destination": destination,
        "route": None,
        "day": None,
        "edge": None,
        "deadline": None,
        "reason": "",
    }


@lru_cache(maxsize=PLANS_KEPT)
def plan_during(origin: str, destination: str, bucket: int) -> list[Row]:
    """Plans one saved trip once per bucket of time.

    Args:
        origin: Where the trip starts.
        destination: Where it ends.
        bucket: The PLAN_TTL-wide window.

    Returns:
        The planner's rows.
    """
    return plan_trip("", ends_only(origin, destination))


def plan_saved(code: str | None) -> list[Planned]:
    """Plans every trip saved against one code.

    Args:
        code: The user's code, or None.

    Returns:
        One entry per saved trip, oldest first.
    """
    now = now_in_boston()

    planned = []
    for trip in read_trips(code):
        bucket = int(time.monotonic() // PLAN_TTL)
        rows = plan_during(trip["origin"], trip["destination"], bucket)

        # The risk pill and the chance beside it
        found = risk_for(rows, now) if rows else None

        planned.append(
            {
                "id": trip["id"],
                "origin": trip["origin"],
                "destination": trip["destination"],
                "card": trip_card(rows) if rows else None,
                "risk": found["level"] if found else None,
                "chance": found["chance"] if found else None,
            }
        )

    return planned
