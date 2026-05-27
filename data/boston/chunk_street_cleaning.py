"""Build street-cleaning chunks from the raw Boston CSV."""

import csv
import json
from pathlib import Path
from typing import Any

from data.chunk_types import StreetCleaningChunk, StreetCleaningMetadata

ROOT = Path(__file__).resolve().parent.parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "chunks"

# Weekday flag columns
DAY_COLUMNS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]

# Week-of-month ordinals
WEEK_ORDINALS = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th", 5: "5th"}

# Raw "side" values mapped to sentence fragment.
SIDE_PHRASES = {
    "even": "on the even-numbered side",
    "odd": "on the odd-numbered side",
    "median": "on the median",
    "even side median": "on the median",
    "odd side median": "on the median",
    "both": "on both sides",
}

# Load the raw street-cleaning rows.
segments: list[dict[str, Any]] = list(
    csv.DictReader(
        (RAW / "boston_street_cleaning.csv").open(encoding="utf-8", newline="")
    )
)

print(f"Loaded {len(segments)} segments from boston_street_cleaning.csv")


def trim_cell(value: str) -> str | None:
    """Trims a cell value, returning None when it is blank.

    Args:
        value: A raw CSV cell.

    Returns:
        The trimmed string, or None if empty.
    """
    return value.strip() or None


def sweep_days(record: dict[str, Any]) -> list[str]:
    """Returns the weekday names a segment is cleaned on.

    Args:
        record: A raw CSV row.

    Returns:
        Weekday names (e.g. ["Monday", "Thursday"]).
    """
    return [day.capitalize() for day in DAY_COLUMNS if record[day] == "t"]


def sweep_weeks(record: dict[str, Any]) -> list[int]:
    """Returns which weeks of the month a segment is cleaned.

    Args:
        record: A raw CSV row.

    Returns:
        Week-of-month numbers (e.g. [1, 3]).
    """
    return [number for number in range(1, 6) if record[f"week_{number}"] == "t"]


def join_phrase(items: list[str]) -> str:
    """Joins strings into a readable list.

    Args:
        items: Ordered strings.

    Returns:
        "A", "A and B", or "A, B, and C".
    """
    if len(items) <= 1:
        return "".join(items)
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return f"{', '.join(items[:-1])}, and {items[-1]}"


def schedule_text(every_day: bool, days: list[str], weeks: list[int]) -> str:
    """Builds the recurrence phrase for the cleaning sentence.

    Args:
        every_day: Whether the segment is cleaned every day, every week.
        days: Weekday names.
        weeks: Week-of-month numbers.

    Returns:
        A phrase like "every day", "Mondays", or "Mondays and Thursdays,
        on the 1st and 3rd weeks of the month".
    """
    if every_day:
        return "every day"
    days_text = join_phrase([f"{day}s" for day in days])
    if len(weeks) == 5:
        return days_text
    weeks_text = join_phrase([WEEK_ORDINALS[number] for number in weeks])
    noun = "week" if len(weeks) == 1 else "weeks"
    return f"{days_text}, on the {weeks_text} {noun} of the month"


def side_text(side: str | None) -> str:
    """Maps a raw side value to its sentence fragment.

    Args:
        side: The raw "side" cell, or None when blank.

    Returns:
        A fragment like "on the even-numbered side", or "" for blank values.
    """
    if side is None:
        return ""
    return SIDE_PHRASES.get(side.lower(), "")


def location_text(
    street: str,
    from_street: str | None,
    to_street: str | None,
    neighborhood: str | None,
) -> str:
    """Builds the opening sentence locating the street segment.

    Args:
        street: Street name.
        from_street: Segment start cross-street, or None.
        to_street: Segment end cross-street, or None.
        neighborhood: Boston neighborhood, or None.

    Returns:
        A sentence like "Ackley Pl between Washington St and Dead End,
        Jamaica Plain."
    """
    parts = [street]
    if from_street and to_street:
        parts.append(f"between {from_street} and {to_street}")
    elif from_street:
        parts.append(f"from {from_street}")
    elif to_street:
        parts.append(f"to {to_street}")
    location = " ".join(parts)
    if neighborhood:
        location = f"{location}, {neighborhood}"
    return f"{location}."


def render_segment(
    record: dict[str, Any],
    every_day: bool,
    days: list[str],
    weeks: list[int],
) -> StreetCleaningChunk:
    """Builds one street-cleaning chunk: rule text and metadata fields.

    Args:
        record: A raw CSV row.
        every_day: Whether the segment is cleaned every day, every week.
        days: Weekday names the segment is cleaned on.
        weeks: Week-of-month numbers the segment is cleaned.

    Returns:
        A dict with:
        - id: "street-cleaning:{main_id}"
        - text: location, cleaning schedule, parking restriction, season
        - metadata: structured fields the parking-rules reads to answer
          whether a spot is being cleaned right now
    """
    street = record["st_name"].strip()
    from_street = trim_cell(record["from"])
    to_street = trim_cell(record["to"])
    neighborhood = trim_cell(record["dist_name"])
    side = trim_cell(record["side"])
    year_round = record["year_round"] == "t"
    start_time = record["start_time"]
    end_time = record["end_time"]

    # Build sentences: location, cleaning schedule, parking restriction, season
    sentences = [location_text(street, from_street, to_street, neighborhood)]
    schedule = schedule_text(every_day, days, weeks)
    sentences.append(f"Street cleaning {schedule}, {start_time} - {end_time}.")
    clause = side_text(side)
    restriction = "No parking" + (f" {clause}" if clause else "")
    sentences.append(f"{restriction} during posted hours.")
    if year_round:
        sentences.append("Year-round.")

    text = " ".join(sentences)

    metadata: StreetCleaningMetadata = {
        "main_id": int(record["main_id"]),
        "street": street,
        "from_street": from_street,
        "to_street": to_street,
        "neighborhood": neighborhood,
        "district": trim_cell(record["dist"]),
        "side": side,
        "start_time": start_time,
        "end_time": end_time,
        "days": days,
        "weeks": weeks,
        "every_day": every_day,
        "year_round": year_round,
        "one_way": record["one_way"] == "t",
        "north_end_pilot": record["north_end_pilot"] == "t",
        "miles": float(record["miles"]),
    }

    return {
        "id": f"street-cleaning:{record['main_id']}",
        "text": text,
        "metadata": metadata,
    }


# Build segment chunks, skipping rows with no day, week, or every-day flag.
segment_chunks = []
for record in segments:
    every_day = record["every_day"] == "t"
    days = sweep_days(record)
    weeks = sweep_weeks(record)
    if every_day or (days and weeks):
        segment_chunks.append(render_segment(record, every_day, days, weeks))

with (OUT / "street_cleaning.jsonl").open("w", encoding="utf-8", newline="\n") as f:
    for chunk in segment_chunks:
        f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

print(f"Wrote {len(segment_chunks)} segment chunks -> chunks/street_cleaning.jsonl")
