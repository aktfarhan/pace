"""Read and write the places saved against a code."""

import secrets
from typing import TypedDict

from data.schema import connect

READ = "SELECT id, label, address FROM saved_places WHERE code = %s ORDER BY id;"
ADD = """
    INSERT INTO saved_places (code, label, address)
    VALUES (%s, %s, %s)
    RETURNING id, label, address;
"""

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
    """One place saved."""

    id: int
    label: str
    address: str


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
        row: An (id, label, address) row.

    Returns:
        The place in an object.
    """
    place_id, label, address = row
    return {"id": place_id, "label": label, "address": address}


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
        cursor.execute(ADD, (against, label, address))
        row = cursor.fetchone()

    return {"code": against, "place": shaped(row)}
