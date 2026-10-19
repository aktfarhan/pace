"""Scrape the MBTA GTFS timetable tables into data/raw/gtfs/."""

import hashlib
import os
import shutil
import zipfile
from pathlib import Path

import httpx

from backend.planner.days import build_all, days_missing

ROOT = Path(__file__).resolve().parent.parent.parent
OUT_DIR = ROOT / "data" / "raw" / "gtfs"
GTFS_URL = "https://cdn.mbta.com/MBTA_GTFS.zip"

# Where a new download waits until every table is complete
STAGING_DIR = OUT_DIR.with_name("gtfs.new")

# Bytes read or written at once
PIECE = 1 << 20

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


def checksum(path: Path) -> str:
    """Reads a file's checksum a piece at a time.

    Args:
        path: The file.

    Returns:
        Its SHA-256, as hex.
    """
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while piece := source.read(PIECE):
            digest.update(piece)
    return digest.hexdigest()


def download(path: Path) -> None:
    """Streams the timetable archive to disk.

    Args:
        path: Where the archive goes.
    """
    with httpx.stream("GET", GTFS_URL, timeout=120) as response:
        response.raise_for_status()
        with path.open("wb") as archive_file:
            for piece in response.iter_bytes(PIECE):
                archive_file.write(piece)


def extract(archive: zipfile.ZipFile, table: str, path: Path) -> tuple[str, int]:
    """Copies one table out of the archive a piece at a time.

    Args:
        archive: The open archive.
        table: The table's filename.
        path: Where the table goes.

    Returns:
        Tuple of (SHA-256 as hex, row count).
    """
    digest = hashlib.sha256()
    lines = 0
    with archive.open(table) as source, path.open("wb") as table_file:
        while piece := source.read(PIECE):
            digest.update(piece)
            lines += piece.count(b"\n")
            table_file.write(piece)
    return digest.hexdigest(), lines - 1


def refresh() -> bool:
    """Downloads the timetable and swaps it once every table is complete.

    Returns:
        Whether any table changed.
    """
    # Every new table is written in full before any live one changes
    shutil.rmtree(STAGING_DIR, ignore_errors=True)
    STAGING_DIR.mkdir(parents=True)
    archive_path = STAGING_DIR / "MBTA_GTFS.zip"
    download(archive_path)

    changed = []
    with zipfile.ZipFile(archive_path) as archive:
        for table in TABLES:
            staged = STAGING_DIR / table
            digest, rows = extract(archive, table, staged)
            live = OUT_DIR / table
            if live.exists() and checksum(live) == digest:
                staged.unlink()
                print(f"  {table}: {rows:,} rows, unchanged")
                continue
            changed.append(table)
            print(f"  {table}: {rows:,} rows, {staged.stat().st_size / 1_000_000:.1f} MB")
    archive_path.unlink()

    # The watched table goes last
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for table in sorted(changed, key=lambda name: name == WATCHED):
        os.replace(STAGING_DIR / table, OUT_DIR / table)
    shutil.rmtree(STAGING_DIR, ignore_errors=True)

    # New calendars with the same stop times still need a reload
    if changed and WATCHED not in changed:
        os.utime(OUT_DIR / WATCHED)

    # The ready-made days follow the tables
    if changed or days_missing():
        print(f"  days: {build_all()} schedule patterns written")

    return bool(changed)


if __name__ == "__main__":
    print(f"Scraping MBTA GTFS -> {OUT_DIR}")
    if refresh():
        print(f"Saved the changed tables to {OUT_DIR}")
    else:
        print("The timetable is already current")
