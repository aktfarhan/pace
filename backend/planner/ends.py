"""Read each end of a trip as a point and the stops that serve it."""

from typing import TypedDict

import psycopg

from backend.geocode import distance_km, resolve

INFINITY = float("inf")

# Meters a second on foot
WALK_PACE = 1.4

# Streets run longer than a straight line
WALK_DETOUR = 1.3

# The longest walk offered at either end of a trip
MAX_WALK_SECONDS = 25 * 60

# How far apart the map and the timetable can mark one station
SAME_STATION_METERS = 100


class Endpoint(TypedDict):
    """One end of a trip, and the stops that serve it."""

    label: str
    point: tuple[float, float]
    walks: dict
    stations: set


def walk_between(start: tuple, end: tuple) -> int:
    """Times the walk between two points.

    Args:
        start: The first point, as (lat, lon).
        end: The second point, as (lat, lon).

    Returns:
        Walking seconds, with the street detour added.
    """
    meters = distance_km(start[0], start[1], end) * 1000
    return int(meters * WALK_DETOUR / WALK_PACE)


def nearby_platforms(lat: float, lon: float, positions: dict) -> dict:
    """Finds the stops close enough to walk to from a point.

    Args:
        lat: The point's latitude.
        lon: The point's longitude.
        positions: stop_id -> (lat, lon) for every boardable stop.

    Returns:
        stop_id -> walk_seconds, for the stops inside the walking cap.
    """
    nearby = {}
    for stop, position in positions.items():
        walk_seconds = walk_between((lat, lon), position)
        if walk_seconds <= MAX_WALK_SECONDS:
            nearby[stop] = walk_seconds
    return nearby


def resolve_endpoint(
    cursor: psycopg.Cursor, text: str, names: dict, children: dict, positions: dict
) -> Endpoint | None:
    """Reads one end of a trip as a place on the map.

    Args:
        cursor: An open cursor on the database.
        text: The endpoint the classifier read.
        names: stop_id -> name for every stop.
        children: parent station id -> boarding platform ids.
        positions: stop_id -> (lat, lon) for every boardable stop.

    Returns:
        The endpoint, or None when the text names no place.
    """
    found = resolve(text, cursor=cursor)
    if found is None:
        return None

    point = (found["lat"], found["lon"])

    # The map and the timetable mark some stations meters apart
    parent = None
    if found["kind"] == "station":
        parent = found["place_id"].removeprefix("station:")
    else:
        for station, platforms in children.items():
            if names[station] != found["label"]:
                continue

            # The distance to the nearest platform
            closest = INFINITY
            for platform in platforms:
                meters = distance_km(*positions[platform], point) * 1000
                closest = min(closest, meters)
            if closest <= SAME_STATION_METERS:
                parent = station
                break

    # A station is boarded where it stands
    if parent is not None:
        walks = {}
        for platform in children.get(parent, [parent]):
            walks[platform] = 0
        return Endpoint(
            label=found["label"], point=point, walks=walks, stations={parent}
        )

    return Endpoint(
        label=found["label"],
        point=point,
        walks=nearby_platforms(point[0], point[1], positions),
        stations=set(),
    )


def trip_times(legs: list[dict], origin: Endpoint, destination: Endpoint) -> tuple:
    """Times the whole trip, with the walk at each end added.

    Args:
        legs: The journey's legs in travel order.
        origin: Where the trip starts.
        destination: Where the trip ends.

    Returns:
        Tuple of (start_stop, end_stop, depart_seconds, arrive_seconds).
    """
    first, last = legs[0], legs[-1]
    start_stop = first["board_stop"] if first["kind"] == "ride" else first["from_stop"]
    end_stop = last["alight_stop"] if last["kind"] == "ride" else last["to_stop"]
    return (
        start_stop,
        end_stop,
        first["depart_seconds"] - origin["walks"].get(start_stop, 0),
        last["arrive_seconds"] + destination["walks"].get(end_stop, 0),
    )
