"""Read a question with the trained model."""

import json
import re
import sys
import unicodedata
from datetime import date, datetime
from difflib import get_close_matches
from functools import lru_cache
from pathlib import Path
from typing import TypedDict

import joblib

from backend.core.clock import now_in_boston
from backend.mbta.stations import station_words
from backend.planner.timetable import gtfs_stamp, read_table, service_date_at

ROOT = Path(__file__).resolve().parent.parent.parent
ARTIFACT = ROOT / "models" / "artifacts" / "parser.pkl"

# What each kind of schedule question sets
KINDS = {"first": ("first", False), "last": ("last", False), "both": ("both", False),
    "howoften": (None, True), "none": (None, False)}

MONTH_NAMES = ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")
MONTHS = {month: number for number, month in enumerate(MONTH_NAMES, 1)}

# Day words the tagger marks, and the day each one means
WEEKDAYS = {day[:3]: day for day in ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")}

# How close a misspelled weekday has to be
DAY_CUTOFF = 0.7

# Relative day words by how they start, and the day each one means
RELATIVE = [("tom", "tomorrow"), ("tmrw", "tomorrow"), ("tmr", "tomorrow"), ("tonight", "tonight"), ("tonite", "tonight"),
    ("evening", "tonight"), ("today", "today"), ("morning", "today"), ("afternoon", "today"), ("weekend", "saturday")]

# Dates inside a day phrase: "nov 16", "11/16"
MONTH = rf"(?P<month>{'|'.join(MONTH_NAMES)})[a-z]*"
DATES = [
    re.compile(rf"{MONTH}\s+(?P<day>\d{{1,2}})(?:st|nd|rd|th)?(?:\s+(?P<year>\d{{4}}))?"),
    re.compile(rf"(?P<day>\d{{1,2}})(?:st|nd|rd|th)?\s+(?:of\s+)?{MONTH}"),
    re.compile(r"(?P<month>\d{1,2})/(?P<day>\d{1,2})(?:/(?P<year>\d{2}|\d{4}))?"),
]

# Words around a route that aren't its name
ROUTE_FILLER = {"the", "bus", "buses", "route", "rt", "train", "trains", "trolley", "subway", "branch", "line", "#"}

# Words that are never a place
NOT_PLACES = {"me", "here", "there", "it", "you", "us"}

# Words that name a vehicle
VEHICLE_WORDS = {"train", "trains", "bus", "buses", "ferry", "boat", "trolley", "t", "line", "lines", "subway",
    "which", "what"}

# Line colors as typed, and shorthand for whole lines
COLORS = {"red": "red", "orange": "orange", "orng": "orange", "blue": "blue", "blu": "blue", "bloo": "blue",
    "green": "green", "grn": "green", "gren": "green", "silver": "silver", "mattapan": "mattapan"}
LINE_SHORTHAND = {"rl": "red line", "ol": "orange line", "bl": "blue line", "gl": "green line", "sl": "silver line",
    "redline": "red line", "commuter train": "commuter rail", "purple line": "commuter rail", "cape flyer": "capeflyer"}

# The name a two-name Commuter Rail line goes by
RAIL_LINES = {"providence", "worcester", "franklin", "newburyport"}

# Verbs that say whether a later time is for leaving or arriving
TIME_VERBS = {"leave", "leaving", "depart", "departing", "go", "going", "head", "be", "arrive", "arriving", "reach",
    "make", "catch"}

# Small words that sit inside long place names
NAME_JOINERS = {"of", "the", "de"}

# Words for an apartment or floor inside an address
UNIT_WORDS = {"apt", "apartment", "unit", "ste", "suite", "fl", "floor", "rm", "room"}

# Words that end a town written after an address
PLACE_ENDS = {"to", "from", "by", "at", "before", "after", "arrive", "arriving", "leave", "leaving", "on", "in",
    "and", "then", "today", "tonight", "tomorrow", ",", ".", "?", "!", ";"}

# Most words a town after a comma can have
TOWN_WORDS = 2

# The state, written after a town
STATES = {"ma", "mass", "massachusetts"}

# Words a town after a comma never has
NOT_TOWNS = {"how", "what", "when", "where", "which", "who", "is", "are", "do", "does", "can", "i", "please", "pls",
    "thanks", "get", "go", "the", "a"}

# A zip code
ZIP = re.compile(r"\d{5}")

# A clock time inside a time phrase
CLOCK = re.compile(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?|(noon|midnight)")


class ParsedQuery(TypedDict):
    """The parser's read of one question."""

    intent: str
    origin: str | None
    destination: str | None
    route: str | None
    day: str | None
    edge: str | None
    deadline: str | None
    reason: str
    leave_at: str | None
    headway: bool


def words_of(query: str) -> list[str]:
    """Splits a question into the words the model reads.

    Args:
        query: The user's question.

    Returns:
        Lowercase words, with punctuation marks as their own words.
    """
    text = query.lower().replace("’", "'")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"\b([ap])\.m\.?", r"\1m", text)
    text = re.sub(r"(\d)\s+(am|pm)\b", r"\1\2", text)
    text = text.replace("'", "")
    return re.findall(r"[a-z0-9:/&#\-]+|[,.?!;]", text)


@lru_cache(maxsize=1)
def bus_names(scraped_at: float) -> frozenset[str]:
    """Reads every bus's short name.

    Args:
        scraped_at: When the tables were scraped.

    Returns:
        Short names like "77", "sl1".
    """
    names = set()
    for row in read_table("routes.txt"):
        if row["route_type"] == "3" and not row["route_id"].startswith("Shuttle"):
            names.add(row["route_short_name"].lower())
    names.discard("")
    return frozenset(names)


def word_shape(word: str) -> str:
    """Reads a word's shape.

    Args:
        word: One word.

    Returns:
        Digits as 0 and letters as a.
    """
    shape = re.sub(r"[0-9]+", "0", word)
    return re.sub(r"[a-z]+", "a", shape)


def token_features(words: list[str], at: int, stations: frozenset, buses: frozenset) -> dict:
    """Describes one word and its neighbors for the tagger.

    Args:
        words: The question's words.
        at: The word's position.
        stations: Words that appear in station names.
        buses: Bus short names.

    Returns:
        Feature name -> value.
    """
    word = words[at]
    features = {
        "w": word,
        "shape": word_shape(word),
        "suffix": word[-3:],
        "station_word": word in stations,
        "bus_name": word in buses,
        "first": at == 0,
        "last": at == len(words) - 1,
    }
    for step in (-3, -2, -1, 1, 2, 3):
        other = words[at + step] if 0 <= at + step < len(words) else "<edge>"
        features[f"w{step:+d}"] = other
        features[f"station{step:+d}"] = other in stations
        features[f"shape{step:+d}"] = word_shape(other)
    verbs = [other for other in words[:at] if other in TIME_VERBS]
    features["verb"] = verbs[-1] if verbs else "<none>"
    features["w-1|w+1"] = f"{features['w-1']}|{features['w+1']}"
    features["w-1|w"] = f"{features['w-1']}|{word}"
    features["w-2|w-1"] = f"{features['w-2']}|{features['w-1']}"
    features["w|w+1"] = f"{word}|{features['w+1']}"
    return features


def neighbor_features(tags: list[str], at: int) -> dict:
    """Describes the first pass's labels around one word.

    Args:
        tags: The first pass's label for each word.
        at: The word's position.

    Returns:
        Feature name -> label.
    """
    features = {}
    for step in (-2, -1, 0, 1, 2):
        other = tags[at + step] if 0 <= at + step < len(tags) else "<edge>"
        features[f"tag{step:+d}"] = other
    return features


def tag_words(model: dict, words: list[str]) -> list[str]:
    """Labels each word as a place, route, time, day or nothing.

    Args:
        model: The loaded bundle.
        words: The question's words.

    Returns:
        One label per word.
    """
    if not words:
        return []
    stations = station_words(gtfs_stamp())
    buses = bus_names(gtfs_stamp())
    first = [token_features(words, at, stations, buses) for at in range(len(words))]
    guesses = list(model["first_pass"].predict(first))
    second = [first[at] | neighbor_features(guesses, at) for at in range(len(words))]
    return list(model["tagger"].predict(second))


def spans(words: list[str], tags: list[str]) -> dict[str, str]:
    """Joins the first run of words under each label.

    Args:
        words: The question's words.
        tags: One label per word.

    Returns:
        Label -> its words.
    """
    tags = list(tags)
    places = ("ORIG", "DEST")

    # The day number after a month
    for at in range(1, len(words)):
        if words[at].isdigit() and tags[at - 1] == "DAY" and words[at - 1][:3] in MONTHS:
            tags[at] = "DAY"

    # A joiner between two place words belongs to the first place
    for at in range(1, len(words) - 1):
        if words[at] in NAME_JOINERS and tags[at] == "O" and tags[at - 1] in places and tags[at + 1] in places:
            tags[at] = tags[at - 1]

    # A house number belongs to its address
    for at in range(len(words) - 1):
        if tags[at] == "ROUTE" and words[at].isdigit() and tags[at + 1] in places and (at == 0 or tags[at - 1] == "O"):
            tags[at] = tags[at + 1]

    # An apartment number belongs to its address
    for at in range(1, len(words)):
        if tags[at - 1] not in places:
            continue
        if words[at] in UNIT_WORDS and at + 1 < len(words):
            tags[at] = tags[at + 1] = tags[at - 1]
        elif words[at].startswith("#") and len(words[at]) > 1:
            tags[at] = tags[at - 1]

    # A town after a comma belongs to its address
    for at in range(1, len(words) - 1):
        if words[at] != "," or tags[at - 1] not in places or not words[at + 1].isalpha():
            continue
        end, town = at + 1, 0
        while end < len(words) and words[end] not in PLACE_ENDS and words[end] not in NOT_TOWNS and (
            tags[end] in ("O", tags[at - 1]) or (tags[end] == "DAY" and ZIP.fullmatch(words[end]))
        ):
            town += words[end] not in STATES and not ZIP.fullmatch(words[end])
            end += 1
        if town <= TOWN_WORDS:
            for inside in range(at, end):
                tags[inside] = tags[at - 1]

    # One place name keeps one label
    for at in range(1, len(words)):
        if tags[at] in places and tags[at - 1] in places:
            tags[at] = tags[at - 1]

    # A word like "it" is no place
    for at, word in enumerate(words):
        alone = (at == 0 or tags[at - 1] != tags[at]) and (at + 1 == len(words) or tags[at + 1] != tags[at])
        if tags[at] in places and word in NOT_PLACES and alone:
            tags[at] = "O"

    found: dict[str, str] = {}
    run: list[str] = []
    label = "O"
    for word, tag in zip([*words, ""], [*tags, "O"]):
        if tag == label and tag != "O":
            run.append(word)
            continue
        if run and label not in found:
            found[label] = " ".join(run)
        run = [word] if tag != "O" else []
        label = tag
    return found


def route_text(phrase: str | None, buses: frozenset = frozenset()) -> str | None:
    """Writes a tagged route the way the route matcher reads it.

    Args:
        phrase: Words like "the ol", "77", "b branch" or "silver line 1".
        buses: Bus short names; when given, a number must be one of them.

    Returns:
        "orange line", "77", "green line b", "sl1" style, or None.
    """
    if not phrase:
        return None
    words = [word for word in phrase.replace("#", " ").split() if word != "the"]

    # "train" or "which line" names no route
    if all(word in VEHICLE_WORDS for word in words):
        return None

    # "providence/stoughton line" is the Providence line
    for at, word in enumerate(words):
        if "/" in word and not word[0].isdigit():
            words[at] = next((part for part in word.split("/") if part in RAIL_LINES), word)
    text = " ".join(words)
    if text in LINE_SHORTHAND:
        return LINE_SHORTHAND[text]

    # A bus by number keeps just its name
    if words[0][0].isdigit():
        return None if buses and words[0] not in buses else words[0]
    if re.fullmatch(r"(?:sl|ct)\d|slw", words[0]):
        return words[0]

    # "silver line 1" and "sl 1"
    match = re.fullmatch(r"(?:silver(?: line)?|sl) ?([1-5]|w)", text)
    if match:
        return f"sl{match.group(1)}"

    # Green Line branches: "green line b", "b line", "green b", "e"
    if text in ("b", "c", "d", "e"):
        return f"green line {text}"
    branch = r"(?:(?:green|grn|gl)(?: line)? ([bcde])|([bcde]) (?:line|branch|train)s?)(?: branch| line)?"
    match = re.fullmatch(branch, text)
    if match:
        return f"green line {match.group(1) or match.group(2)}"

    kept = [word for word in words if word not in ROUTE_FILLER]
    if kept and kept[0] in COLORS and len(kept) == 1:
        return f"{COLORS[kept[0]]} line"
    if text in ("commuter rail", "capeflyer"):
        return text
    if words[-1] in ("line", "branch") and kept:
        return " ".join(kept) + " line"
    return text if words[-1] == "ferry" else None


def place_text(phrase: str | None) -> str | None:
    """Drops what a tagged place can't be.

    Args:
        phrase: Words the tagger marked as a place.

    Returns:
        The place, or None.
    """
    if not phrase:
        return None
    place = phrase.removeprefix("the ").strip(" ,")
    return None if place in NOT_PLACES else place


def clock_text(phrase: str | None) -> str | None:
    """Finds the clock time in a tagged time phrase.

    Args:
        phrase: Words like "by 9am" or "leave at 5:30 pm".

    Returns:
        "9:00 AM" style, or None.
    """
    if not phrase:
        return None
    for match in CLOCK.finditer(phrase):
        if match.group(4):
            return "12:00 PM" if match.group(4) == "noon" else "12:00 AM"
        
        # "in 20 min" is a wait
        if re.match(r"\s*(?:m|min|mins|minutes?|h|hrs?|hours?)\b", phrase[match.end() :]):
            continue

        hour, minute, meridiem = int(match.group(1)), int(match.group(2) or 0), match.group(3)
        if hour > 23 or minute > 59 or (meridiem and not 1 <= hour <= 12):
            continue

        # No am or pm: 24-hour times, else 7 to 11 is morning
        if meridiem is None:
            if hour >= 13 or hour == 0:
                meridiem = "pm" if hour >= 12 else "am"
                hour = hour - 12 if hour > 12 else hour or 12
            else:
                meridiem = "am" if 7 <= hour <= 11 else "pm"
        return f"{hour}:{minute:02d} {meridiem.upper()}"
    return None


def day_text(phrase: str | None, today: date) -> str | None:
    """Turns a tagged day phrase into a day word or a date.

    Args:
        phrase: Words like "on saturday", "nov 16" or "tomorrow night".
        today: Today's service date.

    Returns:
        "saturday", "today", "tonight", "tomorrow" or "YYYY-MM-DD", or None.
    """
    if not phrase:
        return None

    # A written date, the next time it comes round
    for pattern in DATES:
        match = pattern.search(phrase)
        if match is None:
            continue
        month = match.group("month")
        month = int(month) if month.isdigit() else MONTHS[month[:3]]
        year = match.groupdict().get("year")
        try:
            if year:
                year = int(year) + 2000 if len(year) == 2 else int(year)
                return date(year, month, int(match.group("day"))).isoformat()
            asked = date(today.year, month, int(match.group("day")))
            if asked < today:
                asked = date(today.year + 1, month, int(match.group("day")))
            return asked.isoformat()
        except ValueError:
            continue

    # A weekday, then the relative words, then a misspelled weekday
    words = phrase.split()
    for word in words:
        if word[:3] in WEEKDAYS:
            return WEEKDAYS[word[:3]]
    for start, day in RELATIVE:
        if any(word.startswith(start) for word in words):
            return day
    for word in words:
        close = get_close_matches(word.rstrip("s"), WEEKDAYS.values(), n=1, cutoff=DAY_CUTOFF)
        if close:
            return close[0]
    return None


@lru_cache(maxsize=1)
def _load(saved_at: float) -> dict | None:
    """Reads the parser from disk.

    Args:
        saved_at: When it was written.

    Returns:
        The saved bundle, or None.
    """
    try:
        return joblib.load(ARTIFACT)
    except Exception as error:
        print(f"parse: {ARTIFACT.name} unreadable, {error}")
        return None


def trained() -> dict | None:
    """Loads the parser.

    Returns:
        The saved bundle, or None.
    """
    try:
        return _load(ARTIFACT.stat().st_mtime)
    except OSError:
        return None


def read_model(query: str, now: datetime, model: dict | None = None) -> tuple[ParsedQuery, float]:
    """Reads a question with the trained model.

    Args:
        query: The user's question.
        now: The time of the question.
        model: The bundle, or None to load the saved one.

    Returns:
        Tuple of (the read, how sure the model is of the intent).
    """
    model = model or trained()
    words = words_of(query)
    text = " ".join(words)

    # Intent, and which schedule question it is
    if model is None or not words:
        sure, intent, kind = 0.0, "off-topic", "none"
    else:
        chances = model["intent"].predict_proba([text])[0]
        best = int(chances.argmax())
        sure, intent = float(chances[best]), str(model["intent"].classes_[best])
        kind = str(model["kind"].predict([text])[0])

        # Only schedule questions ask for a first, last or how often
        schedule = list(model["intent"].classes_).index("schedule")
        if kind != "none" and intent != "schedule" and chances[schedule] >= 0.25:
            sure, intent = float(chances[schedule]), "schedule"

    # Each word's label, then the words under each label
    found = spans(words, tag_words(model, words)) if model and words else {}

    # A lone time read as a place, like "at noon", is a leave time
    for label in ("ORIG", "DEST"):
        if label in found and CLOCK.fullmatch(found[label]):
            clock = found.pop(label)
            if "LEAVE" not in found and "ARRIVE" not in found:
                found["LEAVE"] = clock
    edge, headway = KINDS[kind]

    parsed: ParsedQuery = {
        "intent": intent,
        "origin": place_text(found.get("ORIG")),
        "destination": place_text(found.get("DEST")),
        "route": route_text(found.get("ROUTE"), bus_names(gtfs_stamp())),
        "day": day_text(found.get("DAY"), service_date_at(now)),
        "edge": edge,
        "deadline": clock_text(found.get("ARRIVE")),
        "reason": "read by the parser model",
        "leave_at": clock_text(found.get("LEAVE")),
        "headway": headway,
    }
    return parsed, sure


def read_question(query: str) -> ParsedQuery:
    """Reads a question with the model.

    Args:
        query: The user's question.

    Returns:
        The parsed query: intent + trip details.
    """
    parsed, sure = read_model(query, now_in_boston())
    print(f"question: read as {parsed['intent']} ({sure:.2f})")
    return parsed


if __name__ == "__main__":
    read, sure = read_model(sys.argv[1], now_in_boston())
    print(json.dumps(read, indent=2))
    print(f"sure: {sure:.2f}")
