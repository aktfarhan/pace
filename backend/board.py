"""Plan every trip saved against a code."""

from datetime import datetime
from typing import TypedDict

from backend.cards import TripCard, trip_card
from backend.classify import ParsedQuery
from backend.planner.trip import plan_trip
from backend.risk import label_for
from backend.trips import read_trips


class Planned(TypedDict):
    """One saved trip and the plan it has right now."""

    id: int
    origin: str
    destination: str
    card: TripCard | None
    risk: str | None


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


def plan_saved(code: str | None) -> list[Planned]:
    """Plans every trip saved against one code.

    Args:
        code: The user's code, or None.

    Returns:
        One entry per saved trip, oldest first.
    """
    now = datetime.now()

    planned = []
    for trip in read_trips(code):
        rows = plan_trip("", ends_only(trip["origin"], trip["destination"]))
        planned.append(
            {
                "id": trip["id"],
                "origin": trip["origin"],
                "destination": trip["destination"],
                "card": trip_card(rows) if rows else None,
                "risk": label_for(rows, now) if rows else None,
            }
        )

    return planned
