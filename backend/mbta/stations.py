"""Find the stations a piece of text names."""

import re
from difflib import get_close_matches
from functools import lru_cache
from typing import TypedDict

from backend.geo.normalize import SUFFIXES, normalize_street
from backend.planner.timetable import gtfs_stamp, read_table

# Shorthand riders type, and the station name it stands for
ALIASES = {
    "bby": "back bay",
    "dtx": "downtown crossing",
    "dtc": "downtown crossing",
    "gov center": "government center",
    "govt center": "government center",
    "gov ctr": "government center",
    "north sta": "north station",
    "south sta": "south station",
    "mass ave": "massachusetts ave",
    "dudley": "nubian",
    "mfa": "museum of fine arts",
    "hynes": "hynes convention center",
    "tufts medical": "tufts medical center",
    "st marys": "st marys st",
    "malden": "malden center",
    "sullivan": "sullivan sq",
    "coolidge": "coolidge corner",
    "bu east": "boston university east",
    "bu central": "boston university central",
    "tufts med": "tufts medical center",
}

# Words after a name that still mean the station
TRAILING = ("station", "sta", "stop", "sq", "t stop", "t station")

# Words typed for the same thing
SPELLINGS = {"ctr": "center", "centre": "center", "&": "and"}

# Slash parts too vague to name a station alone
VAGUE_PARTS = {"495", "route 495", "central", "east braintree"}

# Street type words; "boylston st" is a street, not Boylston station
STREET_WORDS = set(SUFFIXES.values()) - {"sq"}

# The same words as one pattern
STREET_PATTERN = "|".join(sorted(STREET_WORDS))

# How close a misspelled name has to be
FUZZY_CUTOFF = 0.82

# Longest text the misspelling check reads, in words
FUZZY_WORDS = 4


class Station(TypedDict):
    """One station from the timetable."""

    id: str
    name: str
    lat: float
    lon: float


def normalize(text: str) -> str:
    """Puts a name or typed text into one shape for matching.

    Args:
        text: A station name or what the user typed.

    Returns:
        Lowercase words, type words shortened, slashes and dashes as spaces.
    """
    text = re.sub(r"[/\-,?!.()]", " ", text.lower())
    words = [SPELLINGS.get(word, word) for word in text.split()]
    return normalize_street(" ".join(words))


@lru_cache(maxsize=1)
def station_index(scraped_at: float) -> tuple[dict[str, Station], list[str]]:
    """Reads every station and the names it answers to.

    Args:
        scraped_at: When the tables were scraped.

    Returns:
        Tuple of (name -> station, names longest first).
    """
    named: dict[str, Station] = {}
    parts: dict[str, list[Station]] = {}
    for row in read_table("stops.txt"):
        if row["location_type"] != "1":
            continue
        station = Station(
            id=row["stop_id"],
            name=row["stop_name"],
            lat=float(row["stop_lat"]),
            lon=float(row["stop_lon"]),
        )
        named[normalize(row["stop_name"])] = station

        # Each half of a slash name ("Kendall/MIT")
        if "/" in row["stop_name"]:
            for part in row["stop_name"].split("/"):
                key = normalize(part)
                if key and key not in VAGUE_PARTS:
                    parts.setdefault(key, []).append(station)

    # A part counts only when one station has it and no full name does
    for key, stations in parts.items():
        if len(stations) == 1 and key not in named:
            named[key] = stations[0]

    # Shorthand points at a station already named
    for alias, target in ALIASES.items():
        alias, target = normalize(alias), normalize(target)
        if target in named and alias not in named:
            named[alias] = named[target]

    return named, sorted(named, key=len, reverse=True)


def without_trailing(text: str) -> str:
    """Drops a trailing "station" or "sq" from normalized text.

    Args:
        text: Normalized text.

    Returns:
        The text without its last station word, or unchanged.
    """
    for word in TRAILING:
        if text.endswith(" " + word):
            return text[: -len(word) - 1]
    return text


def station_named(text: str) -> Station | None:
    """Finds the station a whole piece of text names exactly.

    Args:
        text: A place the parser read.

    Returns:
        The station, or None when the text is not just a station name.
    """
    named, _ = station_index(gtfs_stamp())
    key = normalize(text).removeprefix("the ")
    if key in named:
        return named[key]
    return named.get(without_trailing(key))


def find_stations(text: str | None) -> list[Station]:
    """Finds every station named inside a piece of text.

    Args:
        text: A place the parser read, or None.

    Returns:
        The stations, longest name first, each span of text used once.
    """
    if not text:
        return []
    named, longest_first = station_index(gtfs_stamp())
    key = normalize(text)

    # Longest names first
    found = []
    claimed = []
    for name in longest_first if not key[:1].isdigit() else []:
        for match in re.finditer(rf"\b{re.escape(name)}\b(?! (?:{STREET_PATTERN})\b)", key):
            span = range(match.start(), match.end())
            if any(set(span) & set(taken) for taken in claimed):
                continue
            claimed.append(span)
            if named[name] not in found:
                found.append(named[name])
    if found:
        return found

    # A misspelling of one short name
    whole = key.removeprefix("the ")
    for typed in (whole, without_trailing(whole)):
        words = typed.split()
        if len(words) > FUZZY_WORDS or (words and words[-1] in STREET_WORDS):
            continue
        close = get_close_matches(typed, longest_first, n=1, cutoff=FUZZY_CUTOFF)
        if close:
            return [named[close[0]]]
    return []


@lru_cache(maxsize=1)
def station_words(scraped_at: float) -> frozenset[str]:
    """Reads every word in a station's name or shorthand.

    Args:
        scraped_at: When the tables were scraped.

    Returns:
        Lowercase words.
    """
    named, _ = station_index(scraped_at)
    words = {word for name in named for word in name.split()}
    for row in read_table("stops.txt"):
        if row["location_type"] == "1":
            words.update(re.findall(r"[a-z0-9]+", row["stop_name"].lower().replace("'", "")))
    return frozenset(words)
