"""Scrape the MBTA GTFS timetable tables into data/raw/gtfs/."""

import io
import os
import shutil
import zipfile
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent.parent
OUT_DIR = ROOT / "data" / "raw" / "gtfs"
GTFS_URL = "https://cdn.mbta.com/MBTA_GTFS.zip"

# Where a new download waits until every table is complete
STAGING_DIR = OUT_DIR.with_name("gtfs.new")

# Tables the planner reads
TABLES = [
    "stops.txt",
    "routes.txt",
    "trips.txt",
    "stop_times.txt",
    "calendar.txt",
    "calendar_dates.txt",
    "transfers.txt",
]

# The table the server watches to know the timetable changed
WATCHED = "stop_times.txt"


def refresh() -> bool:
    """Downloads the timetable and swaps it once every table is complete.

    Returns:
        Whether any table changed.
    """
    response = httpx.get(GTFS_URL, timeout=120)
    response.raise_for_status()
    archive = zipfile.ZipFile(io.BytesIO(response.content))

    # Every new table is written in full before any live one changes
    shutil.rmtree(STAGING_DIR, ignore_errors=True)
    STAGING_DIR.mkdir(parents=True)
    changed = []
    for table in TABLES:
        data = archive.read(table)
        rows = data.count(b"\n") - 1
        live = OUT_DIR / table
        if live.exists() and live.read_bytes() == data:
            print(f"  {table}: {rows:,} rows, unchanged")
            continue
        (STAGING_DIR / table).write_bytes(data)
        changed.append(table)
        print(f"  {table}: {rows:,} rows, {len(data) / 1_000_000:.1f} MB")

    # The watched table goes last
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for table in sorted(changed, key=lambda name: name == WATCHED):
        os.replace(STAGING_DIR / table, OUT_DIR / table)
    shutil.rmtree(STAGING_DIR, ignore_errors=True)

    # New calendars with the same stop times still need a reload
    if changed and WATCHED not in changed:
        os.utime(OUT_DIR / WATCHED)

    return bool(changed)


if __name__ == "__main__":
    print(f"Scraping MBTA GTFS -> {OUT_DIR}")
    if refresh():
        print(f"Saved the changed tables to {OUT_DIR}")
    else:
        print("The timetable is already current")
