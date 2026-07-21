"""Scrape the MBTA GTFS timetable tables into data/raw/gtfs/."""

import io
import zipfile
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent.parent
OUT_DIR = ROOT / "data" / "raw" / "gtfs"
GTFS_URL = "https://cdn.mbta.com/MBTA_GTFS.zip"

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

print(f"Scraping MBTA GTFS -> {OUT_DIR}")

# The feed
response = httpx.get(GTFS_URL, timeout=120)
response.raise_for_status()
archive = zipfile.ZipFile(io.BytesIO(response.content))

# Extract each table
OUT_DIR.mkdir(parents=True, exist_ok=True)
for table in TABLES:
    data = archive.read(table)
    (OUT_DIR / table).write_bytes(data)
    rows = data.count(b"\n") - 1
    print(f"  {table}: {rows:,} rows, {len(data) / 1_000_000:.1f} MB")

print(f"Saved {len(TABLES)} tables to {OUT_DIR}")
