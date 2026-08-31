"""Read the station a saved place walks to."""

from typing import TypedDict

import psycopg

from backend.planner.ends import Endpoint
from backend.timetable import gtfs_stamp, load_route_order

INFINITY = float("inf")

STATION_ROUTES = """
    SELECT metadata->>'stop_id', metadata->'routes'
    FROM chunks WHERE kind = 'stop' AND metadata->>'location_type' = '1';
"""


class Station(TypedDict):
    """The station a place walks to."""

    name: str
    route_id: str
    walk_seconds: int


def station_lines(cursor: psycopg.Cursor) -> dict:
    """Reads the line each station is labelled by.

    Args:
        cursor: An open cursor on the database.

    Returns:
        station_id -> route_id, the best-ranked route serving it.
    """
    # How the MBTA ranks the routes
    order = load_route_order(gtfs_stamp())
    cursor.execute(STATION_ROUTES)

    # Each station takes the best-ranked route serving it
    lines = {}
    for station, routes in cursor.fetchall():
        ranked = None
        for route in routes or []:
            if route not in order:
                continue

            # The first rankable route, then anything better
            if ranked is None or order[route] < order[ranked]:
                ranked = route

        # A station served only by buses is left out
        if ranked is not None:
            lines[station] = ranked

    return lines


def nearest_station(
    end: Endpoint, names: dict, parents: dict, lines: dict
) -> Station | None:
    """Reads the station a resolved place walks to.

    Args:
        end: The saved place.
        names: stop_id -> name for every stop.
        parents: platform id -> parent station id.
        lines: station_id -> the route it is labelled by.

    Returns:
        The nearest station carrying a line, or None.
    """
    # The shortest walk to a station
    closest = None
    walk_seconds = INFINITY
    for stop, seconds in end["walks"].items():
        # Only a platform belonging to a station counts
        station = parents.get(stop)
        if station is None or station not in lines:
            continue

        # Update the best
        if seconds < walk_seconds:
            closest = station
            walk_seconds = seconds

    if closest is None:
        return None

    return Station(
        name=names[closest], route_id=lines[closest], walk_seconds=walk_seconds
    )
