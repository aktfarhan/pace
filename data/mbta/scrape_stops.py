"""Scrape all MBTA stops into data/raw/stops.json."""

import json
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

# Reads the .env
load_dotenv()

ROOT = Path(__file__).resolve().parent.parent.parent
OUT_PATH = ROOT / "data" / "raw" / "stops.json"
API_KEY = os.environ["MBTA_API_KEY"]
BASE_URL = "https://api-v3.mbta.com"
PAGE_LIMIT = 200

print(f"Scraping MBTA stops -> {OUT_PATH.name}")

# Paginate until we get a short page (< 200)
all_stops = []
offset = 0
while True:
    # Fetch one page
    response = httpx.get(
        f"{BASE_URL}/stops",
        params={
            "page[limit]": PAGE_LIMIT,
            "page[offset]": offset,
            "include": "connecting_stops",
        },
        headers={"X-API-Key": API_KEY},
    )
    response.raise_for_status()

    # Extract stops and append
    page = response.json()["data"]
    all_stops.extend(page)

    print(f"  offset={offset}, got {len(page)}, total={len(all_stops)}")

    # Stop on short page
    if len(page) < PAGE_LIMIT:
        break
    offset += PAGE_LIMIT

# Save raw objects
with OUT_PATH.open("w", newline="\n") as f:
    json.dump(all_stops, f, indent=2)

print(f"Saved {len(all_stops)} stops to {OUT_PATH}")
