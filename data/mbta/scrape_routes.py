"""Scrape MBTA routes and map route -> stop into data/raw/."""

import json
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

# Reads the .env
load_dotenv()

ROOT = Path(__file__).resolve().parent.parent.parent
ROUTES_PATH = ROOT / "data" / "raw" / "routes.json"
ROUTE_STOPS_PATH = ROOT / "data" / "raw" / "route_stops.json"
API_KEY = os.environ["MBTA_API_KEY"]
BASE_URL = "https://api-v3.mbta.com"

print(f"Scraping MBTA routes -> {ROUTES_PATH.name}, {ROUTE_STOPS_PATH.name}")

# Fetch all routes
response = httpx.get(f"{BASE_URL}/routes", headers={"X-API-Key": API_KEY})
response.raise_for_status()
routes = response.json()["data"]
print(f"  Got {len(routes)} routes")

# Save routes
with ROUTES_PATH.open("w", newline="\n") as f:
    json.dump(routes, f, indent=2)

# Build route -> stop_ids map
route_stops = {}
for route in routes:
    # Fetch this route's stops
    route_id = route["id"]
    response = httpx.get(
        f"{BASE_URL}/stops",
        params={"filter[route]": route_id},
        headers={"X-API-Key": API_KEY},
    )
    response.raise_for_status()

    # Extract stop IDs and store
    stop_ids = [stop["id"] for stop in response.json()["data"]]
    route_stops[route_id] = stop_ids

    print(f"  {route_id}: {len(stop_ids)} stops")

# Save the mapping
with ROUTE_STOPS_PATH.open("w", newline="\n") as f:
    json.dump(route_stops, f, indent=2)

print(
    f"Saved {len(routes)} routes, {sum(len(v) for v in route_stops.values())} route->stop links"
)
