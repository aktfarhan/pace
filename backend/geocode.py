"""Resolve typed text to one place, address, or street."""

import re
import sys
from typing import TypedDict

import psycopg

from data.places.normalize import normalize_street
from data.schema import connect

# Trigram floor for a row to be a match
WORD_SIMILARITY = "0.45"

# Shortest query that can name a place
MIN_LENGTH = 2

# An apartment or suite on the end of an address
UNIT = re.compile(r"\s+(apt|apartment|unit|ste|suite|fl|floor|#)\s*\d[\w-]*$")

# The state
STATE = re.compile(r"^(ma|mass|massachusetts)$")

# A zip, with or without its four
ZIP = re.compile(r"^\d{5}(-\d{4})?$")

# Half a house number
FRACTION = re.compile(r"^\d+/\d+$")

# The compass words a street name can end on and how they are stored
DIRECTIONS = {"east": "e", "west": "w", "north": "n", "south": "s"}

# Bonus added by a row's kind
STATION_BONUS = 0.25
TOWN_BONUS = 0.15

# Bonus for a wikipedia entry
NOTABLE_BONUS = 0.30

# Rows under one name that make it a chain
CHAIN_ROWS = 5

# Kilometers per degree at Boston's latitude
KM_PER_LAT = 111.0
KM_PER_LON = 82.5

# Free distance, then the cost per kilometer
FREE_KM = 10.0
PER_KM = 0.01

# Score a place must beat for a street name to lose
PLACE_WINS = 1.005

# Boston, for ranking when the caller gives no location
DOWNTOWN = (42.3554, -71.0605)

SET_THRESHOLD = "SELECT set_config('pg_trgm.word_similarity_threshold', %s, false);"
CANDIDATES = """
    SELECT id, display, name, kind, lat, lon, notable, town_id,
           similarity(name, %s) AS score
    FROM places WHERE %s <%% name;
"""
PLACE_NAMED = "SELECT 1 FROM places WHERE name = %s LIMIT 1;"
TOWN_NAMED = "SELECT id FROM towns WHERE name = %s;"
NEIGHBORHOOD_NAMED = """
    SELECT town_id FROM places
    WHERE kind = 'neighborhood' AND name = %s AND town_id IS NOT NULL
    ORDER BY power((lat - %s) * 111.0, 2) + power((lon - %s) * 82.5, 2) ASC,
             id ASC
    LIMIT 1;
"""
STREET_MATCH = """
    SELECT display, lat, lon, similarity(name, %s) AS score FROM streets
    WHERE %s <%% name AND (%s::integer IS NULL OR town_id = %s::integer)
    ORDER BY score DESC,
             power((lat - %s) * 111.0, 2) + power((lon - %s) * 82.5, 2) ASC
    LIMIT 1;
"""
ADDRESS_MATCH = """
    SELECT a.number_text, s.display, t.display, a.lat, a.lon
    FROM address_points a
    JOIN streets s ON a.street_id = s.id
    JOIN towns t ON s.town_id = t.id
    WHERE s.name = %s AND a.number = %s
      AND (%s::integer IS NULL OR s.town_id = %s::integer)
    ORDER BY power((a.lat - %s) * 111.0, 2) + power((a.lon - %s) * 82.5, 2) ASC,
             a.number_text ASC
    LIMIT 1;
"""
CHAIN_LOCATIONS = """
    SELECT id, display, lat, lon, kind FROM places
    WHERE name = %s AND (%s::integer IS NULL OR town_id = %s::integer);
"""

# A candidate row: (id, display, name, kind, lat, lon, notable, town_id, score)
Row = tuple[str, str, str, str, float, float, bool, int | None, float]


class Place(TypedDict):
    """Where one typed query points."""

    place_id: str | None
    label: str
    kind: str
    lat: float
    lon: float


def root_id(place_id: str) -> str:
    """Drops the alias index off a place id.

    Args:
        place_id: A places row id.

    Returns:
        The id of the feature.
    """
    parts = place_id.split(":")
    return ":".join(parts[:3])


def normalize_query(query: str) -> str:
    """Puts typed text into the shape the stored names use.

    Args:
        query: What the user typed.

    Returns:
        Lowercase, no commas, no leading article, type words shortened.
    """
    text = query.lower().strip().replace(",", " ")
    text = UNIT.sub("", text.strip())
    return normalize_street(re.sub(r"^the ", "", text.strip()))


def distance_km(lat: float, lon: float, near: tuple[float, float]) -> float:
    """Measures how far a place is from a reference point.

    Args:
        lat: The point's latitude.
        lon: The point's longitude.
        near: The reference point, as (lat, lon).

    Returns:
        Distance in kilometers.
    """
    north = (lat - near[0]) * KM_PER_LAT
    east = (lon - near[1]) * KM_PER_LON
    return (north * north + east * east) ** 0.5


def peel_town(
    cursor: psycopg.Cursor, words: list[str], near: tuple[float, float]
) -> tuple[list[str], int | None]:
    """Splits a trailing town or neighborhood off the query.

    Args:
        cursor: An open cursor on the database.
        words: The cleaned query, split on spaces.
        near: The reference point, as (lat, lon).

    Returns:
        Tuple of (words left, the town id named or None).
    """
    # A whole name is never split
    cursor.execute(PLACE_NAMED, (" ".join(words),))
    if cursor.fetchone():
        return words, None

    # A trailing state or zip comes off first
    while len(words) > 1 and (STATE.match(words[-1]) or ZIP.match(words[-1])):
        words = words[:-1]

    # Two-word names before one-word names
    for size in (2, 1):
        if len(words) <= size:
            continue

        tail = " ".join(words[-size:])

        # A town by that name
        cursor.execute(TOWN_NAMED, (tail,))
        found = cursor.fetchone()
        if found:
            return words[:-size], found[0]

        # The nearest neighborhood by that name
        cursor.execute(NEIGHBORHOOD_NAMED, (tail, near[0], near[1]))
        found = cursor.fetchone()
        if found:
            return words[:-size], found[0]

    # Nothing matched
    return words, None


def score(row: Row, near: tuple[float, float]) -> float:
    """Ranks one candidate row.

    Args:
        row: A candidate row.
        near: The reference point, as (lat, lon).

    Returns:
        Its text score, adjusted for kind, notability, and distance.
    """
    _, _, _, kind, lat, lon, notable, _, similarity = row

    # Add bonuses
    total = similarity
    if kind == "station":
        total += STATION_BONUS
    elif kind == "town":
        total += TOWN_BONUS

    # Notability only separates ordinary places
    if notable and kind == "place":
        total += NOTABLE_BONUS

    # Only the kilometers past the free zone get the penalty
    return total - max(0.0, distance_km(lat, lon, near) - FREE_KM) * PER_KM


def rank(
    cursor: psycopg.Cursor,
    text: str,
    town_id: int | None,
    near: tuple[float, float],
) -> list[tuple[float, Row]]:
    """Orders every place matching the cleaned query.

    Args:
        cursor: An open cursor on the database.
        text: The cleaned query.
        town_id: A town to stay inside, or None.
        near: The reference point, as (lat, lon).

    Returns:
        Pairs of (score, row), best first, one row per name.
    """
    cursor.execute(CANDIDATES, (text, text))
    rows = cursor.fetchall()

    # Filter by town if available
    if town_id is not None:
        inside = []
        for row in rows:
            if row[7] == town_id:
                inside.append(row)
        rows = inside or rows

    # Filter by matching each word with the name
    words = text.split()
    strict = []
    for row in rows:
        if all(word in row[2] for word in words):
            strict.append(row)

    # Score the filtered rows
    scored = []
    for row in strict or rows:
        scored.append((score(row, near), row))

    # Sort by score, tied -> sort by id
    scored.sort(key=lambda pair: (-pair[0], pair[1][0]))

    # Remove duplicates, keep best
    seen = set()
    ordered = []
    for total, row in scored:
        if row[1] in seen:
            continue
        seen.add(row[1])
        ordered.append((total, row))

    return ordered


def find_address(
    cursor: psycopg.Cursor,
    words: list[str],
    town_id: int | None,
    near: tuple[float, float],
) -> Place | None:
    """Reads the query as a street address.

    Args:
        cursor: An open cursor on the database.
        words: The query words, town already peeled off.
        town_id: A town to stay inside, or None.
        near: The reference point, as (lat, lon).

    Returns:
        The address, or None when the query is not one.
    """
    # Check for a number and a street name
    if len(words) < 2:
        return None

    # Check for house number
    house_number = re.match(r"^(\d+)", words[0])
    if not house_number:
        return None

    # Check for fractional address number
    rest = words[1:]
    if rest and FRACTION.match(rest[0]):
        rest = rest[1:]
    if not rest:
        return None

    # Check for compass name ending
    street = normalize_street(" ".join(rest))
    tail = street.rsplit(" ", 1)
    names = [street]
    if len(tail) == 2 and tail[1] in DIRECTIONS:
        names.append(f"{tail[0]} {DIRECTIONS[tail[1]]}")

    # The nearest house at that number on that street
    hits = []
    for name in names:
        cursor.execute(
            ADDRESS_MATCH,
            (name, int(house_number.group(1)), town_id, town_id, near[0], near[1]),
        )
        hits = cursor.fetchall()
        if hits:
            break

    if not hits:
        return None

    number, street_name, town, lat, lon = hits[0]
    return Place(
        place_id=None,
        label=f"{number} {street_name}, {town}",
        kind="address",
        lat=lat,
        lon=lon,
    )


def find_street(
    cursor: psycopg.Cursor,
    text: str,
    best_score: float,
    town_id: int | None,
    near: tuple[float, float],
) -> Place | None:
    """Reads the query as a street the user named.

    Args:
        cursor: An open cursor on the database.
        text: The cleaned query.
        best_score: The best place score, or zero.
        town_id: A town to stay inside, or None.
        near: The reference point, as (lat, lon).

    Returns:
        The street, or None when a place already matches better.
    """
    # A place scoring this high already beats any street
    if best_score >= PLACE_WINS:
        return None

    # The nearest street to match the name
    cursor.execute(STREET_MATCH, (text, text, town_id, town_id, near[0], near[1]))
    found = cursor.fetchone()
    if not found:
        return None

    display, lat, lon, similarity = found

    # Only an exact street name, and only when no place matched
    if similarity < 0.999 or best_score >= similarity:
        return None

    return Place(place_id=None, label=display, kind="street", lat=lat, lon=lon)


def nearest_location(locations: list[tuple], near: tuple[float, float]) -> tuple:
    """Finds the closest location of a chain.

    Args:
        locations: Rows of (id, display, lat, lon, kind).
        near: The reference point, as (lat, lon).

    Returns:
        Tuple of (id, display, lat, lon).
    """
    chosen = None
    closest_km = None
    for place_id, display, lat, lon, _ in locations:
        km = distance_km(lat, lon, near)
        if closest_km is None or (km, place_id) < (closest_km, chosen[0]):
            closest_km = km
            chosen = (place_id, display, lat, lon)
    return chosen


def lookup(
    cursor: psycopg.Cursor, text: str, near: tuple[float, float]
) -> Place | None:
    """Reads a cleaned query as an address, a street, or a place.

    Args:
        cursor: An open cursor on the database.
        text: The cleaned query.
        near: The reference point, as (lat, lon).

    Returns:
        Where the query points, or None.
    """
    cursor.execute(SET_THRESHOLD, (WORD_SIMILARITY,))

    # Check for an address
    words = text.split()
    address = find_address(cursor, words, None, near)
    if address:
        return address

    # Peel the town and check again
    words, town_id = peel_town(cursor, words, near)
    address = find_address(cursor, words, town_id, near)
    if address:
        return address

    # Rank the places
    name = " ".join(words)
    ordered = rank(cursor, name, town_id, near)

    # Check for a street, unless a place scored
    best_score = ordered[0][0] if ordered else 0.0
    street = find_street(cursor, name, best_score, town_id, near)
    if street:
        return street

    if not ordered:
        return None

    # Get the best row
    place_id, display, stored, kind, lat, lon, *_ = ordered[0][1]

    # Check for a chain, and all ordinary places
    cursor.execute(CHAIN_LOCATIONS, (stored, town_id, town_id))
    locations = cursor.fetchall()
    ordinary = all(location[4] == "place" for location in locations)

    if len(locations) >= CHAIN_ROWS and ordinary:
        place_id, display, lat, lon = nearest_location(locations, near)
        kind = "chain"

    return Place(place_id=root_id(place_id), label=display, kind=kind, lat=lat, lon=lon)


def resolve(
    query: str,
    near: tuple[float, float] | None = None,
    cursor: psycopg.Cursor | None = None,
) -> Place | None:
    """Resolves a query to one place, address, or street.

    Args:
        query: What the user typed.
        near: Where to measure from, as (lat, lon).
        cursor: An open cursor on the database.

    Returns:
        Where the query points, or None.
    """
    text = normalize_query(query)
    if len(text) < MIN_LENGTH:
        return None

    near = near or DOWNTOWN
    if cursor is not None:
        return lookup(cursor, text, near)

    # Open one when the caller has none
    with connect() as connection, connection.cursor() as own_cursor:
        return lookup(own_cursor, text, near)


if __name__ == "__main__":
    found = resolve(sys.argv[1])
    if found is None:
        print("no match")
    else:
        print(f"{found['kind']:12} {found['label']}  ({found['lat']}, {found['lon']})")
