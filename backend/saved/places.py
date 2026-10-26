"""Read and write the places saved against a code."""

import secrets
from typing import TypedDict

import psycopg

from backend.geo.geocode import find_place
from backend.geo.streets import Place
from backend.mbta.station import station_for
from backend.core.db import borrow
from backend.saved.keywords import name_key

READ = """
    SELECT id, label, address, station, route_id, walk_seconds
    FROM saved_places WHERE code = %s ORDER BY id;
"""
ADD = """
    INSERT INTO saved_places
        (code, label, address, station, route_id, walk_seconds, lat, lon)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING id, label, address, station, route_id, walk_seconds;
"""
REMOVE = "DELETE FROM saved_places WHERE id = %s AND code = %s;"
SPOTS = """
    SELECT id, label, address, lat, lon
    FROM saved_places WHERE code = %s ORDER BY id;
"""
FILL = "UPDATE saved_places SET lat = %s, lon = %s WHERE id = %s;"

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


class Unfound(Exception):
    """An address to save that can't be found."""


def mint_code() -> str:
    """Makes a code a user can type on another device.

    Returns:
        Two words and eight characters, dash separated.
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

    with borrow() as connection, connection.cursor() as cursor:
        cursor.execute(READ, (code,))
        rows = cursor.fetchall()

    places = []
    for row in rows:
        places.append(shaped(row))

    return places


def look_up(cursor: psycopg.Cursor, address: str) -> Place | None:
    """Finds where a saved address is, taking the best guess when unclear.

    Args:
        cursor: An open cursor on the database.
        address: The address as it was typed.

    Returns:
        The place, or None.
    """
    lookup = find_place(address, cursor=cursor)
    if lookup["place"] is None and lookup["problem"] == "unclear":
        return lookup["choices"][0]
    return lookup["place"]


def saved_spots(code: str | None) -> dict[str, Place]:
    """Reads where each place saved against one code is.

    Args:
        code: The user's code, or None.

    Returns:
        Saved name key -> the place.
    """
    if code is None:
        return {}

    with borrow() as connection, connection.cursor() as cursor:
        cursor.execute(SPOTS, (code,))
        spots = {}
        for place_id, label, address, lat, lon in cursor.fetchall():
            # A name of only marks can't be typed as a word
            key = name_key(label)
            if not key:
                continue

            # A place saved before spots were kept is looked up once
            if lat is None:
                found = look_up(cursor, address)
                if found is None:
                    continue
                lat, lon = found["lat"], found["lon"]
                cursor.execute(FILL, (lat, lon, place_id))

            spots[key] = Place(
                place_id=f"saved:{place_id}",
                label=label,
                kind="saved",
                lat=lat,
                lon=lon,
            )

    return spots


def add_place(
    code: str | None, label: str, address: str, spot: tuple[float, float] | None
) -> Saved:
    """Saves one place, issuing a code where the user has none.

    Args:
        code: The user's code, or None.
        label: What the user calls the place.
        address: Its street address.
        spot: Where the picked suggestion is, as (lat, lon), or None.

    Returns:
        The stored place and the code it belongs to.

    Raises:
        Unfound: When the address can't be found.
    """
    with borrow() as connection, connection.cursor() as cursor:
        # A picked suggestion is already found
        if spot is not None:
            found = Place(
                place_id=None, label=address, kind="address", lat=spot[0], lon=spot[1]
            )
        else:
            found = find_place(address, cursor=cursor)["place"]
        if found is None:
            raise Unfound(address)

        station = station_for(cursor, found)
        against = code or mint_code()
        cursor.execute(
            ADD,
            (
                against,
                label,
                address,
                station["name"] if station else None,
                station["route_id"] if station else None,
                station["walk_seconds"] if station else None,
                found["lat"],
                found["lon"],
            ),
        )
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

    with borrow() as connection, connection.cursor() as cursor:
        cursor.execute(REMOVE, (place_id, code))
