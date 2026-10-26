"""Resolve typed text to one place, address, or street."""

import re
import sys
import threading
from typing import TypedDict

import psycopg

from backend.core.db import borrow
from backend.geo.normalize import normalize_street
from backend.geo.streets import (
    CHOICES,
    STREET_TYPES,
    TOWN_STREET_SIMILARITY,
    Place,
    Town,
    choices_of,
    distance_km,
    forget_areas,
    house_number,
    houses,
    in_area,
    nearest_first,
    pick,
    street_areas,
    street_place,
    streets_named,
)

# Trigram floor for a row to be a match
WORD_SIMILARITY = "0.45"

# A misspelled street with no house number has to be this close
LONE_STREET_SIMILARITY = 0.6

# Shortest query that can name a place
MIN_LENGTH = 2

# An apartment, suite or floor anywhere after the street
UNIT = re.compile(
    r"\s(?:apt|apartment|unit|ste|suite|fl|floor|rm|room)\b\.?\s*#?\s*[\w-]*"
    r"|\s#\s*[\w-]+"
    r"|\s\d+(?:st|nd|rd|th)\s+(?:fl|floor)\b"
)

# The state
STATE = re.compile(r"^(ma|mass|massachusetts)$")

# A zip, with or without its four
ZIP = re.compile(r"^\d{5}(-\d{4})?$")

# Bonus added by a row's kind
STATION_BONUS = 0.25
TOWN_BONUS = 0.15

# Bonus for a wikipedia entry
NOTABLE_BONUS = 0.30

# A mapped area beats a single point with the same name
AREA_BONUS = 0.01

# Rows under one name that make it a chain
CHAIN_ROWS = 5

# Free distance, then the cost per kilometer
FREE_KM = 10.0
PER_KM = 0.01

# Score a place must beat for a street name to lose
PLACE_WINS = 1.005

# A place this close to a street of its name is on that street
SAME_SPOT_KM = 1.0

# Boston, for ranking when the caller gives no location
DOWNTOWN = (42.3554, -71.0605)

# Letters of a street typed before it is suggested
SUGGEST_LETTERS = 3

# Places offered before streets while typing
SUGGESTED_PLACES = 3

REMEMBERED_MAX = 2000

SET_THRESHOLD = """
    SELECT set_config('pg_trgm.word_similarity_threshold', %s, false),
           set_config('pg_trgm.similarity_threshold', %s, false);
"""
CANDIDATES = """
    SELECT id, display, name, kind, lat, lon, notable, town_id,
           similarity(name, %s) AS score
    FROM places WHERE %s <%% name;
"""
PLACE_NAMED = "SELECT 1 FROM places WHERE name = %s LIMIT 1;"
TOWN_NAMED = "SELECT id, display FROM towns WHERE name = %s;"
TOWN_STARTING = "SELECT id, display FROM towns WHERE name LIKE %s ORDER BY length(name), name LIMIT 1;"
NEIGHBORHOOD_NAMED = """
    SELECT town_id, lat, lon, display FROM places
    WHERE kind = 'neighborhood' AND name = %s AND town_id IS NOT NULL
    ORDER BY power((lat - %s) * 111.0, 2) + power((lon - %s) * 82.5, 2) ASC,
             id ASC
    LIMIT 1;
"""
CHAIN_LOCATIONS = """
    SELECT id, display, lat, lon, kind FROM places
    WHERE name = %s AND (%s::integer IS NULL OR town_id = %s::integer);
"""

# A candidate row: (id, display, name, kind, lat, lon, notable, town_id, score)
Row = tuple[str, str, str, str, float, float, bool, int | None, float]


class Lookup(TypedDict):
    """What one typed query found."""

    place: Place | None
    problem: str | None
    choices: list[Place]


# Places already found
_remembered: dict[tuple[str, tuple[float, float]], Lookup] = {}
_remembered_lock = threading.Lock()


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
    text = " " + query.lower().strip().replace(",", " ")
    text = re.sub(r"^\s*(the|near)\s+", " ", text)

    # Units only come off an address
    if re.match(r"^\s*\d", text):
        text = UNIT.sub(" ", text)

    # A picked choice like "near 12 Elm St" keeps its "near"
    if re.match(r"^\s*near\s+\d", query.lower()):
        text = "near " + text.strip()
    return normalize_street(text.strip())


def missed(problem: str, choices: list[Place] | None = None) -> Lookup:
    """Builds the result for a query that found no one place.

    Args:
        problem: "unclear", "outside" or "missing".
        choices: Places to offer instead.

    Returns:
        A lookup with no place.
    """
    return Lookup(place=None, problem=problem, choices=choices or [])


def found(place: Place) -> Lookup:
    """Builds the result for a query that found its place.

    Args:
        place: Where the query points.

    Returns:
        A lookup with the place.
    """
    return Lookup(place=place, problem=None, choices=[])


def peel_town(
    cursor: psycopg.Cursor, words: list[str], near: tuple[float, float]
) -> tuple[list[str], Town | None]:
    """Splits a trailing town or neighborhood off the query.

    Args:
        cursor: An open cursor on the database.
        words: The cleaned query, split on spaces.
        near: The reference point, as (lat, lon).

    Returns:
        Tuple of (words left, the town named or None).
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
        row = cursor.fetchone()
        if row:
            return words[:-size], Town(
                town_id=row[0], display=row[1], near=None, area=row[1]
            )

        # A neighborhood the address data names
        area = street_areas(cursor).get(tail)
        if area:
            return words[:-size], area

        # The nearest neighborhood by that name
        cursor.execute(NEIGHBORHOOD_NAMED, (tail, near[0], near[1]))
        row = cursor.fetchone()
        if row:
            return words[:-size], Town(
                town_id=row[0], display=row[3], near=(row[1], row[2]), area=None
            )

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
    place_id, _, _, kind, lat, lon, notable, _, similarity = row

    # Add bonuses
    total = similarity
    if kind == "station":
        total += STATION_BONUS
    elif kind == "town":
        total += TOWN_BONUS

    # Notability only separates ordinary places
    if notable and kind == "place":
        total += NOTABLE_BONUS

    if kind == "place" and place_id.startswith(("osm:way:", "osm:relation:")):
        total += AREA_BONUS

    # Only the kilometers past the free zone get the penalty
    return total - max(0.0, distance_km(lat, lon, near) - FREE_KM) * PER_KM


def rank(
    cursor: psycopg.Cursor,
    text: str,
    town_id: int | None,
    near: tuple[float, float],
) -> tuple[list[tuple[float, Row]], bool]:
    """Orders every place matching the cleaned query.

    Args:
        cursor: An open cursor on the database.
        text: The cleaned query.
        town_id: A town to stay inside, or None.
        near: The reference point, as (lat, lon).

    Returns:
        Tuple of (pairs of (score, row), best first, one row per name.
    """
    cursor.execute(CANDIDATES, (text, text))
    rows = cursor.fetchall()

    # Filter by town if available
    outside = False
    if town_id is not None:
        inside = []
        for row in rows:
            if row[7] == town_id:
                inside.append(row)
        outside = not inside and bool(rows)
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

    return ordered, outside


def find_address(
    cursor: psycopg.Cursor,
    words: list[str],
    town: Town | None,
    near: tuple[float, float],
    next_door: bool = False,
) -> Lookup:
    """Reads the query as a street address.

    Args:
        cursor: An open cursor on the database.
        words: The query words, town already peeled off.
        town: The town named, or None.
        near: The reference point, as (lat, lon).
        next_door: Whether the house next door was asked for, from a picked choice.

    Returns:
        The address, or why there is none.
    """
    number = words[0]
    town_id = town["town_id"] if town else None
    near = town["near"] if town and town["near"] else near

    streets = houses(cursor, words, town_id, near)

    # Inside a town the exact house beats the one next door
    if town is not None and town["near"] is None and not next_door:
        exact = [street for street in streets if street["exact"]]
        if exact and exact[0]["tier"] == streets[0]["tier"]:
            streets = exact
    streets = in_area(streets, town)

    if streets:
        street, unclear = pick(streets)
        choices = choices_of(nearest_first(street, streets), number)
        if unclear and len(choices) > 1:
            return missed("unclear", choices)
        return found(street_place(street, number))

    # The street without the house
    rest = house_number(words)[1]
    named = in_area(streets_named(cursor, rest, town_id, near), town)

    # The same address in other towns is offered, never used quietly
    if town is not None:
        elsewhere = choices_of(houses(cursor, words, None, near), number)
        if elsewhere:
            same = [street for street in named if street["tier"] >= 2]
            return missed("outside", (choices_of(same, None) + elsewhere)[:CHOICES])
    return missed("missing", choices_of(named, None))


def find_street(
    cursor: psycopg.Cursor,
    words: list[str],
    best: tuple[float, Row] | None,
    town: Town | None,
    near: tuple[float, float],
) -> Lookup | None:
    """Reads the query as a street the user named.

    Args:
        cursor: An open cursor on the database.
        words: The cleaned query's words.
        best: The best place as (score, row), or None.
        town: The town named, or None.
        near: The reference point, as (lat, lon).

    Returns:
        The street, or None when a place already matches better.
    """
    best_score = best[0] if best else 0.0
    town_id = town["town_id"] if town else None
    near = town["near"] if town and town["near"] else near

    # The same name, or a near spelling that says it is a street
    typed_type = words[-1] in STREET_TYPES
    streets = []
    for street in in_area(streets_named(cursor, words, town_id, near), town):
        if street["tier"] == 3 or (
            typed_type
            and street["tier"] == 1
            and street["score"] >= LONE_STREET_SIMILARITY
        ):
            streets.append(street)
    if not streets:
        return None

    # A street in the neighborhood named beats a place of that name elsewhere
    away = False
    if (
        best
        and town
        and town["area"]
        and streets[0]["tier"] == 3
        and streets[0]["area"] == town["area"]
    ):
        away = (
            distance_km(best[1][4], best[1][5], (streets[0]["lat"], streets[0]["lon"]))
            > SAME_SPOT_KM
        )

    # A place scoring this high already beats any street
    if not away and (best_score >= PLACE_WINS or best_score >= streets[0]["score"]):
        return None

    street, unclear = pick(streets)
    if unclear:
        return missed("unclear", choices_of(nearest_first(street, streets), None))
    return found(street_place(street, None))


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


def row_place(row: Row) -> Place:
    """Turns a ranked places row into a place.

    Args:
        row: A candidate row.

    Returns:
        The place.
    """
    place_id, display, _, kind, lat, lon, *_ = row
    return Place(place_id=root_id(place_id), label=display, kind=kind, lat=lat, lon=lon)


def lookup(cursor: psycopg.Cursor, text: str, near: tuple[float, float]) -> Lookup:
    """Reads a cleaned query as an address, a street, or a place.

    Args:
        cursor: An open cursor on the database.
        text: The cleaned query.
        near: The reference point, as (lat, lon).

    Returns:
        Where the query points, or why it points nowhere.
    """
    cursor.execute(SET_THRESHOLD, (WORD_SIMILARITY, str(TOWN_STREET_SIMILARITY)))
    next_door = text.startswith("near ")
    text = text.removeprefix("near ")
    words, town = peel_town(cursor, text.split(), near)

    # A place named like "10 tables" is that place
    cursor.execute(PLACE_NAMED, (text,))
    named = cursor.fetchone() is not None

    # A number and a street is an address
    if house_number(words) and not named:
        return find_address(cursor, words, town, near, next_door)
    
    if town is not None and not words[1:] and house_number(text.split()) and not named:
        return find_address(cursor, text.split(), None, near)

    # Rank the places
    name = " ".join(words)
    ordered, outside = rank(cursor, name, town["town_id"] if town else None, near)

    # Check for a street, unless a place in the town scored
    best = ordered[0] if ordered and not outside else None
    street = find_street(cursor, words, best, town, near)
    if street:
        return street

    # Places by that name lie only in other towns
    if outside:
        return missed("outside", [row_place(row) for _, row in ordered[:CHOICES]])

    if not ordered:
        return missed("missing")

    # Get the best row
    place_id, display, stored, kind, lat, lon, *_ = ordered[0][1]

    # Check for a chain, and all ordinary places
    town_id = town["town_id"] if town else None
    cursor.execute(CHAIN_LOCATIONS, (stored, town_id, town_id))
    locations = cursor.fetchall()
    ordinary = all(location[4] == "place" for location in locations)

    if len(locations) >= CHAIN_ROWS and ordinary:
        place_id, display, lat, lon = nearest_location(locations, near)
        kind = "chain"

    return found(
        Place(place_id=root_id(place_id), label=display, kind=kind, lat=lat, lon=lon)
    )


def suggest_houses(
    cursor: psycopg.Cursor,
    typed: list[str],
    words: list[str],
    town: Town | None,
    near: tuple[float, float],
) -> list[Place]:
    """Lists the houses a half-typed address could become.

    Args:
        cursor: An open cursor on the database.
        typed: The query's words.
        words: The words left after a town came off.
        town: The town named, or None.
        near: The reference point, as (lat, lon).

    Returns:
        Up to CHOICES places, best first.
    """
    # A town still being typed
    if town is None and len(typed) >= 3 and len(typed[-1]) >= SUGGEST_LETTERS:
        cursor.execute(TOWN_STARTING, (typed[-1] + "%",))
        row = cursor.fetchone()
        if row:
            words = typed[:-1]
            town = Town(town_id=row[0], display=row[1], near=None, area=row[1])

    # The town's reading first
    readings = []
    if house_number(words):
        readings.append((words, town))
    if town is not None:
        readings.append((typed, None))

    for reading, named in readings:
        street = " ".join(house_number(reading)[1])
        if sum(letter.isalpha() for letter in street) < SUGGEST_LETTERS:
            continue
        town_id = named["town_id"] if named else None
        point = named["near"] if named and named["near"] else near
        found = in_area(houses(cursor, reading, town_id, point, typing=True), named)
        if found:
            return unique_labels(choices_of(found, reading[0]))
    return []


def unique_labels(places: list[Place]) -> list[Place]:
    """Drops places whose label is already listed.

    Args:
        places: Places, best first.

    Returns:
        Up to CHOICES places, one per label.
    """
    labels = set()
    unique = []
    for place in places:
        if place["label"] not in labels:
            labels.add(place["label"])
            unique.append(place)
    return unique[:CHOICES]


def suggest(
    cursor: psycopg.Cursor, query: str, near: tuple[float, float] | None = None
) -> list[Place]:
    """Lists the places a half-typed query could become.

    Args:
        cursor: An open cursor on the database.
        query: What the user has typed so far.
        near: Where to measure from, as (lat, lon).

    Returns:
        Up to CHOICES places, best first.
    """
    text = normalize_query(query).removeprefix("near ")
    if len(text) < MIN_LENGTH:
        return []

    near = near or DOWNTOWN
    cursor.execute(SET_THRESHOLD, (WORD_SIMILARITY, str(TOWN_STREET_SIMILARITY)))
    words, town = peel_town(cursor, text.split(), near)
    town_id = town["town_id"] if town else None
    if town and town["near"]:
        near = town["near"]

    # An address offers houses on the streets it could mean
    typed = text.split()
    if house_number(typed):
        return suggest_houses(cursor, typed, words, town, near)

    # The best places, then streets, then the other places
    ordered, _ = rank(cursor, " ".join(words), town_id, near)
    places = [row_place(row) for _, row in ordered[:CHOICES]]
    streets = []
    for street in streets_named(cursor, words, town_id, near, typing=True):
        if street["tier"] >= 2:
            streets.append(street_place(street, None))
    offered = (
        places[:SUGGESTED_PLACES]
        + streets[:SUGGESTED_PLACES]
        + places[SUGGESTED_PLACES:]
    )
    return unique_labels(offered)


def forget_places() -> None:
    """Clears the remembered places and neighborhoods."""
    with _remembered_lock:
        _remembered.clear()
    forget_areas()


def find_place(
    query: str,
    near: tuple[float, float] | None = None,
    cursor: psycopg.Cursor | None = None,
) -> Lookup:
    """Finds the one place a query names, or says why there isn't one.

    Args:
        query: What the user typed.
        near: Where to measure from, as (lat, lon).
        cursor: An open cursor on the database.

    Returns:
        The place, or the problem and places to choose from.
    """
    text = normalize_query(query)
    if len(text) < MIN_LENGTH:
        return missed("missing")

    near = near or DOWNTOWN
    key = (text, near)
    with _remembered_lock:
        if key in _remembered:
            return _remembered[key]

    if cursor is not None:
        result = lookup(cursor, text, near)
    else:
        # Open one when the caller has none
        with borrow() as connection, connection.cursor() as own_cursor:
            result = lookup(own_cursor, text, near)

    # The oldest goes first when full
    with _remembered_lock:
        if len(_remembered) >= REMEMBERED_MAX:
            del _remembered[next(iter(_remembered))]
        _remembered[key] = result
    return result


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
    result = find_place(query, near, cursor)

    # An unclear name still has a best guess
    if result["problem"] == "unclear":
        return result["choices"][0]
    return result["place"]


if __name__ == "__main__":
    result = find_place(sys.argv[1])
    place = result["place"]
    if place is None:
        print(f"no match ({result['problem']})")
        for choice in result["choices"]:
            print(f"  choice: {choice['label']}")
    else:
        print(f"{place['kind']:12} {place['label']}  ({place['lat']}, {place['lon']})")
