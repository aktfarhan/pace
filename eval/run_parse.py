"""Question reader: run eval/parse.jsonl through the parser model at a fixed time and score each field."""

import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from backend.assistant.parse import read_model
from backend.core.clock import ZONE
from backend.mbta.stations import find_stations

ROOT = Path(__file__).resolve().parent.parent
PARSE_PATH = ROOT / "eval" / "parse.jsonl"
HOLDOUT_PATH = ROOT / "eval" / "parse_holdout.jsonl"

NOW = datetime(2026, 11, 4, 8, 30, tzinfo=ZONE)

# The fields scored on every row
FIELDS = [
    "origin",
    "destination",
    "route",
    "day",
    "edge",
    "deadline",
    "leave_at",
    "headway",
]


def station_ids(place: str | None) -> list[str]:
    """Lists the stations a place points to."""
    return [station["id"] for station in find_stations(place)]


def same_place(read: str | None, want: str | None) -> bool:
    """Checks a place."""
    if read == want:
        return True
    return bool(read and want) and station_ids(read) == station_ids(want) != []


def score(path: Path, fields: list[str]) -> bool:
    """Scores one file and prints its report.

    Args:
        path: The questions and their answers.
        fields: The fields each row is scored on.

    Returns:
        Whether every row was right.
    """
    rows = [json.loads(line) for line in path.open() if line.strip()]
    print(
        f"Reading {len(rows)} questions from {path.name}, as of {NOW:%a %b %d %Y %I:%M %p}"
    )

    intent_counts = defaultdict(lambda: {"correct": 0, "total": 0})
    field_misses = defaultdict(int)
    station_rows = 0
    station_misses = 0
    failed = []

    for row in rows:
        read, sure = read_model(row["query"], NOW)
        predicted = read["intent"]

        gold = row["intent"]
        intent_counts[gold]["total"] += 1
        problems = []
        if predicted == gold or (predicted == "off-topic" and row.get("hard")):
            intent_counts[gold]["correct"] += 1
        else:
            problems.append(f"intent {gold} -> {predicted} ({sure:.2f})")

        # Each field; off-topic rows are scored on intent alone
        for field in fields if predicted == gold != "off-topic" else []:
            want = row.get(field, False if field == "headway" else None)
            right = (
                same_place(read[field], want)
                if field in ("origin", "destination")
                else read[field] == want
            )
            if not right:
                field_misses[field] += 1
                problems.append(f"{field} {want!r} -> {read[field]!r}")

        # The stations the places point to, when the row lists them
        if "stations" in row and predicted == gold != "off-topic":
            station_rows += 1
            found = []
            for place in (read["origin"], read["destination"]):
                for station in station_ids(place):
                    if station not in found:
                        found.append(station)
            if found != row["stations"]:
                station_misses += 1
                problems.append(f"stations {row['stations']} -> {found}")

        marker = "OK" if not problems else "NO"
        print(f"  [{row['id']}] {marker} {row['query']}")
        for problem in problems:
            print(f"      {problem}")
        if problems:
            failed.append(row["id"])

    total = len(rows)
    correct = total - len(failed)
    print()
    print(f"Overall: {correct}/{total} rows fully right ({100 * correct / total:.1f}%)")
    if failed:
        print(f"  Failed: {', '.join(failed)}")

    print()
    print("Per-intent accuracy:")
    for intent, counts in sorted(intent_counts.items()):
        pct = 100 * counts["correct"] / counts["total"]
        print(f"  {intent:16s} {counts['correct']}/{counts['total']} ({pct:.1f}%)")

    print()
    print("Field accuracy:")
    for field in fields:
        right = total - field_misses[field]
        print(f"  {field:16s} {right}/{total}")
    if station_rows:
        print(f"  {'stations':16s} {station_rows - station_misses}/{station_rows}")
    print()
    return not failed


passed = score(PARSE_PATH, FIELDS)
if "--holdout" in sys.argv:
    score(HOLDOUT_PATH, FIELDS)
sys.exit(0 if passed else 1)
