"""Scrape MBTA LAMP subway performance days into data/raw/lamp/."""

import csv
import io
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent.parent
OUT_DIR = ROOT / "data" / "raw" / "lamp"
INDEX_URL = (
    "https://performancedata.mbta.com/lamp/subway-on-time-performance-v1/index.csv"
)

# How far back to pull service days
DAYS = 365

print(f"Scraping MBTA LAMP -> {OUT_DIR}")

# The index of every published service day
response = httpx.get(INDEX_URL, timeout=60)
response.raise_for_status()
published = list(csv.DictReader(io.StringIO(response.text)))

# The days inside the window
today = datetime.now(timezone.utc).date()
since = (today - timedelta(days=DAYS)).isoformat()
wanted = []
for row in published:
    if row["service_date"] >= since:
        wanted.append(row)

# The days still missing
OUT_DIR.mkdir(parents=True, exist_ok=True)
missing = []
for row in wanted:
    target = OUT_DIR / f"{row['service_date']}.parquet"
    if not target.exists() or target.stat().st_size != int(row["size_bytes"]):
        missing.append((row, target))

# What the fetch will cost
due = sum(int(row["size_bytes"]) for row, _ in missing)
print(f"{len(wanted)} days since {since}, {len(missing)} to fetch, {due / 1e6:.0f} MB")

# One request per missing day
with httpx.Client(timeout=120) as client:
    for number, (row, target) in enumerate(missing, start=1):
        day = client.get(row["file_url"])
        day.raise_for_status()
        target.write_bytes(day.content)
        print(f"  {number}/{len(missing)} {row['service_date']}")

# Everything held after the run
held = sum(path.stat().st_size for path in OUT_DIR.glob("*.parquet"))
print(f"Saved {len(missing)} days, {OUT_DIR} now holds {held / 1e6:.0f} MB")
