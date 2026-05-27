"""Scrape Boston street sweeping schedules into data/raw/boston_street_cleaning.csv."""

from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent.parent
OUT_PATH = ROOT / "data" / "raw" / "boston_street_cleaning.csv"
BASE_URL = "https://data.boston.gov"
# Boston Street Sweeping Schedules data resource ID
RESOURCE_ID = "9fdbdcad-67c8-4b23-b6ec-861e77d56227"

print(f"Scraping Boston street sweeping -> {OUT_PATH.name}")

# Resolve the current CSV download URL from the CKAN API
response = httpx.get(
    f"{BASE_URL}/api/3/action/resource_show", params={"id": RESOURCE_ID}
)
response.raise_for_status()
download_url = response.json()["result"]["url"]
print(f"  Current file: {download_url.rsplit('/', 1)[-1]}")

# Download the CSV the resource points to
response = httpx.get(download_url, follow_redirects=True)
response.raise_for_status()
OUT_PATH.write_bytes(response.content)

row_count = len(response.text.splitlines()) - 1
print(f"Saved {row_count} rows to {OUT_PATH}")
