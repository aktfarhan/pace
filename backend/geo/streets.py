"""Find the streets a typed name could mean, and the houses on them."""

import re
import threading
from typing import TypedDict

import psycopg

from backend.geo.aliases import COMPASS, compass_forms, expand_aliases
from backend.geo.normalize import SUFFIXES, normalize_street

# Trigram floor for a misspelled street name, lower inside a named town
STREET_SIMILARITY = 0.5
TOWN_STREET_SIMILARITY = 0.4

# A house number, with a letter or a range end
HOUSE_NUMBER = re.compile(r"^(\d+)([a-z]?|-\d+[a-z]?)$")

# Half a house number
FRACTION = re.compile(r"^\d+/\d+$")

# The compass words a street name can end on and how they are stored
DIRECTIONS = {"east": "e", "west": "w", "north": "n", "south": "s"}

# Street type words, short and long
STREET_TYPES = frozenset(SUFFIXES) | frozenset(SUFFIXES.values())

# Kilometers per degree at Boston's latitude
KM_PER_LAT = 111.0
KM_PER_LON = 82.5

# Boston's town id; its streets are told apart by neighborhood
BOSTON_TOWN_ID = 35

# How far a missing house number can be from the nearest real one
NEAR_NUMBERS = 40

# A house this close to the number counts as the same as it
NEXT_DOOR = 4

# Streets read for one name
STREET_ROWS = 60
TYPING_ROWS = 200

# Choices offered when a place is unclear or missing
CHOICES = 5
FAR_KM = 25.0

# Two equal matches are clear when the nearest is this much closer
CLEAR_RATIO = 2.0
CLEAR_KM = 1.0

# Match scores this close count as equal
SAME_SCORE = 0.05

# Letters a misspelled street can be off by inside a named town
TYPO_EDITS = 1
LONG_NAME = 8

# Boston streets show their neighborhood
STREET_CANDIDATES = """
    SELECT s.id, s.name, s.display, s.lat, s.lon,
           CASE WHEN s.town_id = %(boston)s AND s.neighborhood IS NOT NULL
                 AND NOT EXISTS (SELECT 1 FROM towns o WHERE o.name = lower(s.neighborhood))
                THEN s.neighborhood ELSE t.display END AS area,
           similarity(s.name, %(street)s) AS score
    FROM streets s JOIN towns t ON t.id = s.town_id
    WHERE (s.name = ANY(%(names)s) OR s.name LIKE %(prefix)s OR s.name %% %(street)s)
      AND (%(town)s::integer IS NULL OR s.town_id = %(town)s::integer)
    ORDER BY (s.name = ANY(%(names)s)) DESC, (s.name LIKE %(prefix)s) DESC,
             (CASE WHEN %(typing)s THEN 0 ELSE similarity(s.name, %(street)s) END) DESC,
             power((s.lat - %(lat)s) * 111.0, 2) + power((s.lon - %(lon)s) * 82.5, 2) ASC
    LIMIT %(rows)s;
"""

# The house on each street nearest the number
NUMBER_ON_STREETS = """
    SELECT DISTINCT ON (a.street_id) a.street_id, a.number_text, a.number, a.lat, a.lon,
           (a.number = %(number)s
            OR (a.number < %(number)s AND a.number_text ~ '^[0-9]+-[0-9]+$'
                AND split_part(a.number_text, '-', 2)::integer >= %(number)s)) AS exact
    FROM address_points a
    WHERE a.street_id = ANY(%(streets)s)
      AND a.number BETWEEN %(number)s - %(gap)s AND %(number)s + %(gap)s
    ORDER BY a.street_id, exact DESC, abs(a.number - %(number)s),
             (a.number_text = %(text)s) DESC, a.number_text ASC;
"""

# Streets in a town holding the house number
STREETS_WITH_NUMBER = """
    SELECT s.id, s.name, s.display, s.lat, s.lon,
           CASE WHEN s.town_id = %(boston)s AND s.neighborhood IS NOT NULL
                 AND NOT EXISTS (SELECT 1 FROM towns o WHERE o.name = lower(s.neighborhood))
                THEN s.neighborhood ELSE t.display END AS area
    FROM streets s JOIN towns t ON t.id = s.town_id
    WHERE s.town_id = %(town)s AND abs(length(s.name) - length(%(street)s)) <= 2
      AND EXISTS (SELECT 1 FROM address_points a
                  WHERE a.street_id = s.id AND a.number = %(number)s);
"""

# Each neighborhood the address data names
STREET_AREAS = """
    SELECT DISTINCT ON (lower(neighborhood)) lower(neighborhood), neighborhood, town_id,
           avg(lat) OVER area, avg(lon) OVER area
    FROM streets WHERE neighborhood IS NOT NULL
    WINDOW area AS (PARTITION BY lower(neighborhood), town_id)
    ORDER BY lower(neighborhood), count(*) OVER area DESC, town_id;
"""


class Place(TypedDict):
    """Where one typed query points."""

    place_id: str | None
    label: str
    kind: str
    lat: float
    lon: float


class Town(TypedDict):
    """A town or neighborhood named at the end of a query."""

    town_id: int
    display: str
    near: tuple[float, float] | None
    area: str | None


class Street(TypedDict):
    """One street a name could mean."""

    display: str
    area: str
    tier: int
    score: float
    exact: bool
    close: bool
    number: str | None
    lat: float
    lon: float
    km: float


# Neighborhoods named in the address data
_areas: dict[str, Town] | None = None
_areas_lock = threading.Lock()


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


def street_areas(cursor: psycopg.Cursor) -> dict[str, Town]:
    """Reads the neighborhoods the address data names.

    Args:
        cursor: An open cursor on the database.

    Returns:
        Lowercase name -> the town it lies in, with its middle.
    """
    global _areas
    with _areas_lock:
        if _areas is None:
            cursor.execute(STREET_AREAS)
            rows = cursor.fetchall()
            _areas = {}
            for name, display, town_id, lat, lon in rows:
                _areas[name] = Town(
                    town_id=town_id, display=display, near=(lat, lon), area=display
                )
        return _areas


def in_area(streets: list[Street], town: Town | None) -> list[Street]:
    """Keeps the streets in the neighborhood named.

    Args:
        streets: Candidate streets.
        town: The town or neighborhood named, or None.

    Returns:
        The streets in that neighborhood, or all.
    """
    if town is None or town["area"] is None:
        return streets
    inside = [street for street in streets if street["area"] == town["area"]]

    # The area never lets a misspelled street beat a street spelled right
    if inside and max(street["tier"] for street in inside) >= max(
        street["tier"] for street in streets
    ):
        return inside
    return streets


def forget_areas() -> None:
    """Clears the remembered neighborhoods."""
    global _areas
    with _areas_lock:
        _areas = None


def edits(first: str, second: str) -> int:
    """Counts the letters added, dropped, changed or swapped between two words.

    Args:
        first: One word.
        second: The other word.

    Returns:
        The number of edits.
    """
    rows = [list(range(len(second) + 1))]
    for i, a in enumerate(first, 1):
        row = [i]
        for j, b in enumerate(second, 1):
            row.append(min(rows[-1][j] + 1, row[j - 1] + 1, rows[-1][j - 1] + (a != b)))
            if i > 1 and j > 1 and a == second[j - 2] and first[i - 2] == b:
                row[j] = min(row[j], rows[-2][j - 2] + 1)
        rows.append(row)
    return rows[-1][-1]


def fix_type_word(words: list[str]) -> list[str]:
    """Corrects a misspelled type word on the end.

    Args:
        words: The street's words.

    Returns:
        The words, with the last one corrected when it is one letter off a type word.
    """
    last = words[-1].lower()
    if len(words) < 2 or len(last) < 4 or last in STREET_TYPES:
        return words
    for type_word in SUFFIXES:
        if edits(last, type_word) == 1:
            return words[:-1] + [type_word]
    return words


def street_names(words: list[str]) -> list[str]:
    """Writes a typed street every way it may be stored.

    Args:
        words: The street's words.

    Returns:
        The names to look for, the typed one first.
    """
    street = expand_aliases(normalize_street(" ".join(fix_type_word(words))))
    names = []
    for form in compass_forms(street):
        names.append(form)

        # A compass word on the end is stored short
        tail = form.rsplit(" ", 1)
        if len(tail) == 2 and tail[1] in DIRECTIONS:
            names.append(f"{tail[0]} {DIRECTIONS[tail[1]]}")
    return list(dict.fromkeys(names))


def compass_of(street: str) -> str | None:
    """Reads the compass word a street name starts with.

    Args:
        street: A street name.

    Returns:
        The short compass letter, or None.
    """
    first = street.split(" ", 1)[0]
    if first in COMPASS:
        return first
    for short, long in COMPASS.items():
        if first == long:
            return short
    return None


def match_tier(stored: str, names: list[str], typing: bool) -> int:
    """Says how well a stored street name matches the typed one.

    Args:
        stored: The stored street name.
        names: The typed name's forms.
        typing: Whether the last word may be cut short.

    Returns:
        3 for the same name, 2 when the type word was left off, 1 for a near
        spelling, 0 for a different compass word.
    """
    if stored in names:
        return 3
    for name in names:
        if stored.startswith(name + " ") or (typing and stored.startswith(name)):
            return 2

    # East Broadway is never a misspelled West Broadway
    if compass_of(stored) != compass_of(names[0]):
        return 0
    return 1


def streets_like(
    cursor: psycopg.Cursor,
    names: list[str],
    town_id: int | None,
    near: tuple[float, float],
    typing: bool = False,
) -> list[tuple]:
    """Reads the streets a typed name could mean.

    Args:
        cursor: An open cursor on the database.
        names: The typed name's forms.
        town_id: A town to stay inside, or None.
        near: The reference point, as (lat, lon).
        typing: Whether the last word may be cut short.

    Returns:
        Rows of (id, name, display, lat, lon, area, score).
    """
    prefix = names[0] + ("%" if typing else " %")
    cursor.execute(
        STREET_CANDIDATES,
        {
            "boston": BOSTON_TOWN_ID,
            "street": names[0],
            "names": names,
            "prefix": prefix,
            "town": town_id,
            "lat": near[0],
            "lon": near[1],
            "typing": typing,
            "rows": TYPING_ROWS if typing else STREET_ROWS,
        },
    )
    return cursor.fetchall()


def spelled_like(
    cursor: psycopg.Cursor, street: str, number: int, town_id: int
) -> list[tuple]:
    """Reads the streets in a town that hold the house and are a letter or two off.

    Args:
        cursor: An open cursor on the database.
        street: The typed street name, normalized.
        number: The house number.
        town_id: The town named.

    Returns:
        Rows of (id, name, display, lat, lon, area, score).
    """
    cursor.execute(
        STREETS_WITH_NUMBER,
        {"boston": BOSTON_TOWN_ID, "town": town_id, "street": street, "number": number},
    )
    allowed = TYPO_EDITS + (len(street) >= LONG_NAME)
    rows = []
    for row in cursor.fetchall():
        count = edits(street, row[1])
        if count <= allowed:
            rows.append((*row, 1 - count / max(len(street), len(row[1]))))
    return rows


def best_per_area(streets: list[Street]) -> list[Street]:
    """Keeps the best street in each town or neighborhood.

    Args:
        streets: Candidate streets.

    Returns:
        One street per area, best first.
    """
    streets.sort(
        key=lambda street: (
            -street["tier"],
            -street["exact"],
            -street["score"],
            street["km"],
        )
    )
    kept = {}
    for street in streets:
        kept.setdefault(street["area"], street)

    # Across areas the house next door counts the same as the exact one
    return sorted(
        kept.values(),
        key=lambda street: (
            -street["tier"],
            not street["close"],
            -street["score"],
            street["km"],
        ),
    )


def pick(streets: list[Street]) -> tuple[Street, bool]:
    """Picks one street, unless two equal matches are about as near.

    Args:
        streets: One street per area, best first.

    Returns:
        Tuple of (the street, whether the choice is unclear).
    """
    best = streets[0]

    # The house next door is never used quietly
    exact = [
        other for other in streets if other["exact"] and other["tier"] == best["tier"]
    ]
    if not best["exact"] and exact:
        return min(exact, key=lambda street: street["km"]), True

    equal = []
    for street in streets:
        if (
            street["tier"] == best["tier"]
            and street["close"] == best["close"]
            and best["score"] - street["score"] < SAME_SCORE
        ):
            equal.append(street)
    equal.sort(key=lambda street: street["km"])

    if len(equal) < 2:
        return best, False

    # The nearest is clear when the next is much farther away
    first, second = equal[0]["km"], equal[1]["km"]
    if second >= CLEAR_RATIO * first and second - first >= CLEAR_KM:
        return equal[0], False

    # Unclear, so the best guess is the nearest exact house among the close ones
    close = []
    for street in equal:
        if street["km"] < CLEAR_RATIO * first or street["km"] - first < CLEAR_KM:
            close.append(street)
    close.sort(key=lambda street: (not street["exact"], street["km"]))
    return close[0], True


def nearest_first(street: Street, streets: list[Street]) -> list[Street]:
    """Moves the picked street to the front of the list.

    Args:
        street: The street pick chose.
        streets: One street per area, best first.

    Returns:
        The same streets, the picked one first.
    """
    return [street] + [other for other in streets if other is not street]


def street_place(street: Street, typed_number: str | None) -> Place:
    """Turns a street, or the house found on it, into a place.

    Args:
        street: The street.
        typed_number: The house number asked for, or None for the street itself.

    Returns:
        The place.
    """
    if typed_number is None:
        label = f"{street['display']}, {street['area']}"
        kind = "street"
    elif street["exact"]:
        label = f"{street['number']} {street['display']}, {street['area']}"
        kind = "address"
    else:
        label = f"near {typed_number} {street['display']}, {street['area']}"
        kind = "address"
    return Place(
        place_id=None, label=label, kind=kind, lat=street["lat"], lon=street["lon"]
    )


def house_number(words: list[str]) -> tuple[re.Match, list[str]] | None:
    """Splits a house number off the front of an address.

    Args:
        words: The query words.

    Returns:
        Tuple of (the number, the street's words), or None.
    """
    if len(words) < 2:
        return None

    number = HOUSE_NUMBER.match(words[0])
    if not number:
        return None

    # Skip a half number
    rest = words[1:]
    if rest and FRACTION.match(rest[0]):
        rest = rest[1:]
    if not rest:
        return None
    return number, rest


def houses(
    cursor: psycopg.Cursor,
    words: list[str],
    town_id: int | None,
    near: tuple[float, float],
    typing: bool = False,
) -> list[Street]:
    """Finds the house an address names on every street it could mean.

    Args:
        cursor: An open cursor on the database.
        words: The query words, town already peeled off.
        town_id: A town to stay inside, or None.
        near: The reference point, as (lat, lon).
        typing: Whether the last word may be cut short.

    Returns:
        One street per area with its house, best first.
    """
    split = house_number(words)
    if split is None:
        return []
    number, rest = split
    names = street_names(rest)
    rows = streets_like(cursor, names, town_id, near, typing)

    # Inside a town, add streets a letter or two off that hold the house
    if town_id is not None and not typing:
        found = {row[0]: row for row in rows}
        for row in spelled_like(cursor, names[0], int(number.group(1)), town_id):
            if row[0] not in found or found[row[0]][6] < row[6]:
                found[row[0]] = row
        rows = list(found.values())
    if not rows:
        return []

    # The nearest house on each street
    by_id = {row[0]: row for row in rows}
    cursor.execute(
        NUMBER_ON_STREETS,
        {
            "number": int(number.group(1)),
            "text": number.group(0).upper(),
            "streets": list(by_id),
            "gap": NEAR_NUMBERS,
        },
    )

    streets = []
    for street_id, number_text, found_number, lat, lon, exact in cursor.fetchall():
        _, name, display, _, _, area, similarity = by_id[street_id]
        tier = match_tier(name, names, typing)

        # A misspelled street needs the exact house
        floor = STREET_SIMILARITY if town_id is None else TOWN_STREET_SIMILARITY
        if tier == 0 or (tier == 1 and (not exact or similarity < floor)):
            continue
        streets.append(
            Street(
                display=display,
                area=area,
                tier=tier,
                score=similarity,
                exact=exact,
                close=exact or abs(found_number - int(number.group(1))) <= NEXT_DOOR,
                number=number_text,
                lat=lat,
                lon=lon,
                km=distance_km(lat, lon, near),
            )
        )
    return best_per_area(streets)


def streets_named(
    cursor: psycopg.Cursor,
    words: list[str],
    town_id: int | None,
    near: tuple[float, float],
    typing: bool = False,
) -> list[Street]:
    """Finds the streets a name could mean.

    Args:
        cursor: An open cursor on the database.
        words: The street's words.
        town_id: A town to stay inside, or None.
        near: The reference point, as (lat, lon).
        typing: Whether the last word may be cut short.

    Returns:
        One street per area, best first.
    """
    names = street_names(words)
    streets = []
    for _, name, display, lat, lon, area, similarity in streets_like(
        cursor, names, town_id, near, typing
    ):
        tier = match_tier(name, names, typing)
        floor = STREET_SIMILARITY if town_id is None else TOWN_STREET_SIMILARITY
        if tier == 0 or (tier == 1 and similarity < floor):
            continue
        streets.append(
            Street(
                display=display,
                area=area,
                tier=tier,
                score=similarity,
                exact=True,
                close=True,
                number=None,
                lat=lat,
                lon=lon,
                km=distance_km(lat, lon, near),
            )
        )
    return best_per_area(streets)


def choices_of(streets: list[Street], typed_number: str | None) -> list[Place]:
    """Lists streets as places to choose from.

    Args:
        streets: One street per area, best first.
        typed_number: The house number asked for, or None.

    Returns:
        Up to CHOICES places.
    """
    nearby = [street for street in streets if street["km"] <= FAR_KM] or streets
    if not nearby:
        return []

    # The houses asked for
    tier = nearby[0]["tier"]
    exact = [street for street in nearby if street["exact"] and street["tier"] == tier]
    if typed_number is not None and len(exact) >= 2:
        nearest = min(street["km"] for street in exact)
        nearer = [
            other for other in nearby if not other["exact"] and other["km"] < nearest
        ]
        nearby = exact[: CHOICES - len(nearer[:1])] + nearer[:1]
    return [street_place(street, typed_number) for street in nearby[:CHOICES]]
