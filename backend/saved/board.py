"""Plan every trip saved against a code."""

import time
from functools import lru_cache
from typing import TypedDict

from backend.assistant.cards import TripCard, trip_card
from backend.assistant.retrieve import Row
from backend.core.clock import now_in_boston
from backend.planner.trip import ends_only, plan_trip
from backend.geo.streets import Place
from backend.reliability.risk import risk_for
from backend.saved.keywords import name_key
from backend.saved.places import saved_spots
from backend.saved.trips import SavedTrip, read_trips

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
    failed: bool


@lru_cache(maxsize=PLANS_KEPT)
def plan_during(origin: str, destination: str, bucket: int, mine: tuple) -> list[Row]:
    """Plans one saved trip once per bucket of time.

    Args:
        origin: Where the trip starts.
        destination: Where it ends.
        bucket: The PLAN_TTL-wide window.
        mine: (key, label, lat, lon) per end with a spot.

    Returns:
        The planner's rows.
    """
    saved = {}
    for key, label, lat, lon in mine:
        saved[key] = Place(place_id=None, label=label, kind="saved", lat=lat, lon=lon)
    return plan_trip("", ends_only(origin, destination), guess=True, saved=saved)


def ends_known(trip: SavedTrip, spots: dict[str, Place]) -> tuple:
    """Collects the spots a saved trip's ends are planned from.

    Args:
        trip: The saved trip.
        spots: The user's saved name key -> place.

    Returns:
        (key, label, lat, lon) per end with a spot.
    """
    mine = []
    ends = (
        (trip["origin"], trip["origin_at"]),
        (trip["destination"], trip["destination_at"]),
    )
    for end, kept in ends:
        key = name_key(end)
        if not key:
            continue

        # A saved name first, then the spot kept with the trip
        spot = spots.get(key)
        if spot is not None:
            mine.append((key, spot["label"], spot["lat"], spot["lon"]))
        elif kept is not None:
            mine.append((key, end, kept[0], kept[1]))
    return tuple(mine)


def plan_saved(code: str | None) -> list[Planned]:
    """Plans every trip saved against one code.

    Args:
        code: The user's code, or None.

    Returns:
        One entry per saved trip, oldest first.
    """
    now = now_in_boston()
    trips = read_trips(code)
    spots = saved_spots(code) if trips else {}

    planned = []
    for trip in trips:
        bucket = int(time.monotonic() // PLAN_TTL)

        # One trip that can't be planned leaves the others alone
        card, found, failed = None, None, False
        try:
            mine = ends_known(trip, spots)
            rows = plan_during(trip["origin"], trip["destination"], bucket, mine)
            if rows:
                card, found = trip_card(rows), risk_for(rows, now)
        except Exception as error:
            print(f"board: trip {trip['id']} failed: {type(error).__name__}: {error}")
            failed = True

        planned.append(
            {
                "id": trip["id"],
                "origin": trip["origin"],
                "destination": trip["destination"],
                "card": card,
                "risk": found["level"] if found else None,
                "chance": found["chance"] if found else None,
                "failed": failed,
            }
        )

    return planned
