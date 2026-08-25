"""Read and write the trips saved against a code."""

from typing import TypedDict

from backend.places import mint_code
from data.schema import connect

READ = "SELECT id, origin, destination FROM saved_trips WHERE code = %s ORDER BY id;"
ADD = """
    INSERT INTO saved_trips (code, origin, destination)
    VALUES (%s, %s, %s)
    RETURNING id, origin, destination;
"""


class SavedTrip(TypedDict):
    """One saved trip."""

    id: int
    origin: str
    destination: str


class Kept(TypedDict):
    """A saved trip and the code it now belongs to."""

    code: str
    trip: SavedTrip


def shaped(row: tuple) -> SavedTrip:
    """Turns one row into a saved trip.

    Args:
        row: An (id, origin, destination) row.

    Returns:
        The trip in an object.
    """
    trip_id, origin, destination = row
    return {"id": trip_id, "origin": origin, "destination": destination}


def read_trips(code: str | None) -> list[SavedTrip]:
    """Reads the trips saved against one code.

    Args:
        code: The user's code, or None.

    Returns:
        The trips, oldest first.
    """
    if code is None:
        return []

    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(READ, (code,))
        rows = cursor.fetchall()

    trips = []
    for row in rows:
        trips.append(shaped(row))

    return trips


def add_trip(code: str | None, origin: str, destination: str) -> Kept:
    """Saves one trip, issuing a code where the user has none.

    Args:
        code: The user's code, or None.
        origin: Where the trip starts.
        destination: Where it ends.

    Returns:
        The stored trip and the code it belongs to.
    """
    against = code or mint_code()

    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(ADD, (against, origin, destination))
        row = cursor.fetchone()

    return {"code": against, "trip": shaped(row)}
