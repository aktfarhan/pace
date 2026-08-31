"""Read and write the places saved against a code."""

import secrets
from typing import TypedDict

from backend.station import station_for
from data.schema import connect

READ = """
    SELECT id, label, address, station, route_id, walk_seconds
    FROM saved_places WHERE code = %s ORDER BY id;
"""
ADD = """
    INSERT INTO saved_places (code, label, address, station, route_id, walk_seconds)
    VALUES (%s, %s, %s, %s, %s, %s)
    RETURNING id, label, address, station, route_id, walk_seconds;
"""
REMOVE = "DELETE FROM saved_places WHERE id = %s AND code = %s;"

# Words a code is built from
WORDS = (
    "amber",
    "anchor",
    "birch",
    "brook",
    "cedar",
    "clay",
    "cobalt",
    "copper",
    "delta",
    "ember",
    "fern",
    "flint",
    "harbor",
    "heron",
    "indigo",
    "ivory",
    "juniper",
    "kettle",
    "lantern",
    "linen",
    "maple",
    "marsh",
    "olive",
    "onyx",
    "otter",
    "pebble",
    "plum",
    "quarry",
    "quartz",
    "raven",
    "rowan",
    "sable",
    "sage",
    "slate",
    "sorrel",
    "spruce",
    "thistle",
    "umber",
    "vetch",
    "willow",
)

# Characters for ids
LETTERS = "23456789abcdefghjkmnpqrstuvwxyz"

# How many of those trail the two words
TAIL = 8


class SavedPlace(TypedDict):
    """One place saved, and the station it walks to."""

    id: int
    label: str
    address: str
    station: str | None
    route_id: str | None
    walk_seconds: int | None


class Saved(TypedDict):
    """A stored place and the code it now belongs to."""

    code: str
    place: SavedPlace


def mint_code() -> str:
    """Makes a code a user can type on another device.

    Returns:
        Two words and four characters, dash separated.
    """
    tail = "".join(secrets.choice(LETTERS) for _ in range(TAIL))
    return f"{secrets.choice(WORDS)}-{secrets.choice(WORDS)}-{tail}"


def shaped(row: tuple) -> SavedPlace:
    """Turns one row into a saved place.

    Args:
        row: An (id, label, address, station, route_id, walk_seconds) row.

    Returns:
        The place in an object.
    """
    place_id, label, address, station, route_id, walk_seconds = row
    return {
        "id": place_id,
        "label": label,
        "address": address,
        "station": station,
        "route_id": route_id,
        "walk_seconds": walk_seconds,
    }


def read_places(code: str | None) -> list[SavedPlace]:
    """Reads the places saved against one code.

    Args:
        code: The user's code, or None.

    Returns:
        The places, oldest first.
    """
    if code is None:
        return []

    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(READ, (code,))
        rows = cursor.fetchall()

    places = []
    for row in rows:
        places.append(shaped(row))

    return places


def add_place(code: str | None, label: str, address: str) -> Saved:
    """Saves one place, issuing a code where the user has none.

    Args:
        code: The user's code, or None.
        label: What the user calls the place.
        address: Its street address.

    Returns:
        The stored place and the code it belongs to.
    """
    against = code or mint_code()

    with connect() as connection, connection.cursor() as cursor:
        found = station_for(cursor, address)

        station = found["name"] if found else None
        route_id = found["route_id"] if found else None
        walk_seconds = found["walk_seconds"] if found else None

        cursor.execute(ADD, (against, label, address, station, route_id, walk_seconds))
        row = cursor.fetchone()

    return {"code": against, "place": shaped(row)}


def remove_place(code: str | None, place_id: int) -> None:
    """Removes one place from a user's code.

    Args:
        code: The user's code, or None.
        place_id: The place to remove.
    """
    if code is None:
        return

    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(REMOVE, (place_id, code))
