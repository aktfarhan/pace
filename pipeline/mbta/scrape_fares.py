"""Scrape MBTA fare amounts from the GTFS feed into data/raw/fares.json."""

import csv
import io
import json
import zipfile
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent.parent
OUT_PATH = ROOT / "data" / "raw" / "fares.json"
GTFS_URL = "https://cdn.mbta.com/MBTA_GTFS.zip"

print(f"Scraping MBTA fares -> {OUT_PATH.name}")

# Fares are inside the GTFS bundle
response = httpx.get(GTFS_URL, timeout=60)
response.raise_for_status()
archive = zipfile.ZipFile(io.BytesIO(response.content))

# One amount per product
fares = {}
with archive.open("fare_products.txt") as product_file:
    # utf-8-sig strips the BOM
    reader = csv.DictReader(io.TextIOWrapper(product_file, encoding="utf-8-sig"))
    for row in reader:
        product_id = row["fare_product_id"]

        # Keep the CharlieCard price
        if product_id not in fares or row["fare_media_id"] == "charliecard":
            fares[product_id] = {
                "name": row["fare_product_name"],
                "amount": float(row["amount"]),
            }

# Save the mapping
with OUT_PATH.open("w", newline="\n") as fares_file:
    json.dump(fares, fares_file, indent=2)

print(f"Saved {len(fares)} fare products to {OUT_PATH}")
