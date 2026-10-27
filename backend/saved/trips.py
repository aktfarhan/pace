"""Read and write the trips saved against a code."""

from typing import TypedDict

from backend.saved.places import mint_code
from backend.core.db import borrow

READ = """
    SELECT id, origin, destination,
        origin_lat, origin_lon, destination_lat, destination_lon
    FROM saved_trips WHERE code = %s ORDER BY id;
"""
ADD = """
    INSERT INTO saved_trips (code, origin, destination,
        origin_lat, origin_lon, destination_lat, destination_lon)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (code, origin, destination) DO UPDATE SET
        origin_lat = COALESCE(EXCLUDED.origin_lat, saved_trips.origin_lat),
        origin_lon = COALESCE(EXCLUDED.origin_lon, saved_trips.origin_lon),
        destination_lat = COALESCE(EXCLUDED.destination_lat, saved_trips.destination_lat),
        destination_lon = COALESCE(EXCLUDED.destination_lon, saved_trips.destination_lon)
    RETURNING id, origin, destination,
        origin_lat, origin_lon, destination_lat, destination_lon;
"""
REMOVE = "DELETE FROM saved_trips WHERE id = %s AND code = %s;"


class SavedTrip(TypedDict):
    """One saved trip, and where its ends are when known."""

    id: int
    origin: str
    destination: str
    origin_at: tuple[float, float] | None
    destination_at: tuple[float, float] | None


class Kept(TypedDict):
    """A saved trip and the code it now belongs to."""

    code: str
    trip: SavedTrip


def shaped(row: tuple) -> SavedTrip:
    """Turns one row into a saved trip.

    Args:
        row: An (id, origin, destination, and both ends' lat and lon) row.

    Returns:
        The trip in an object.
    """
    trip_id, origin, destination, origin_lat, origin_lon, end_lat, end_lon = row
    return {
        "id": trip_id,
        "origin": origin,
        "destination": destination,
        "origin_at": (origin_lat, origin_lon) if origin_lat is not None else None,
        "destination_at": (end_lat, end_lon) if end_lat is not None else None,
    }


def read_trips(code: str | None) -> list[SavedTrip]:
    """Reads the trips saved against one code.

    Args:
        code: The user's code, or None.

    Returns:
        The trips, oldest first.
    """
    if code is None:
        return []

    with borrow() as connection, connection.cursor() as cursor:
        cursor.execute(READ, (code,))
        rows = cursor.fetchall()

    trips = []
    for row in rows:
        trips.append(shaped(row))

    return trips


def add_trip(
    code: str | None,
    origin: str,
    destination: str,
    origin_at: tuple[float, float] | None,
    destination_at: tuple[float, float] | None,
) -> Kept:
    """Saves one trip, issuing a code where the user has none.

    Args:
        code: The user's code, or None.
        origin: Where the trip starts.
        destination: Where it ends.
        origin_at: Where the start is, as (lat, lon), or None.
        destination_at: Where the end is, as (lat, lon), or None.

    Returns:
        The stored trip and the code it belongs to.
    """
    against = code or mint_code()
    origin_lat, origin_lon = origin_at or (None, None)
    end_lat, end_lon = destination_at or (None, None)

    with borrow() as connection, connection.cursor() as cursor:
        cursor.execute(
            ADD,
            (against, origin, destination, origin_lat, origin_lon, end_lat, end_lon),
        )
        row = cursor.fetchone()

    return {"code": against, "trip": shaped(row)}


def remove_trip(code: str | None, trip_id: int) -> bool:
    """Removes one trip from a user's code.

    Args:
        code: The user's code, or None.
        trip_id: The trip to remove.

    Returns:
        Whether there was such a trip to remove.
    """
    if code is None:
        return False

    with borrow() as connection, connection.cursor() as cursor:
        cursor.execute(REMOVE, (trip_id, code))
        return cursor.rowcount > 0
