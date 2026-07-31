"""Load the places table from OSM places, MBTA stations, and street neighborhoods."""

import csv
import json
from pathlib import Path

from data.places.normalize import normalize_street
from data.schema import connect

ROOT = Path(__file__).resolve().parent.parent.parent
PLACES_PATH = ROOT / "data" / "raw" / "places" / "places.jsonl"
STOPS_PATH = ROOT / "data" / "raw" / "gtfs" / "stops.txt"

# Address counts by coordinate and town
TOWN_GRID = """
    SELECT round(p.lat::numeric, 2), round(p.lon::numeric, 2), s.town_id, count(*)
    FROM address_points p JOIN streets s ON s.id = p.street_id
    GROUP BY 1, 2, 3;
"""
STREET_NEIGHBORHOODS = """
    SELECT s.neighborhood, s.town_id, avg(s.lat), avg(s.lon)
    FROM streets s WHERE s.neighborhood IS NOT NULL
    GROUP BY s.neighborhood, s.town_id;
"""
INSERT_PLACE = """
    INSERT INTO places (id, kind, category, name, display, address,
                        station_id, town_id, lat, lon, notable, source)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
"""

# OSM categories that name part of a town
NEIGHBOURHOOD_CATEGORIES = {
    "neighbourhood",
    "suburb",
    "quarter",
    "borough",
    "hamlet",
    "village",
}

# OSM categories that name a whole municipality
TOWN_CATEGORIES = {"town", "city"}


def build_grid(cursor) -> tuple[dict, dict]:
    """Maps coordinates to the town with the most addresses.

    Args:
        cursor: An open cursor on the database.

    Returns:
        Tuple of (fine, coarse): town id by coordinate.
    """
    fine, coarse = {}, {}
    fine_best = {}
    coarse_totals = {}

    cursor.execute(TOWN_GRID)
    for lat, lon, town_id, count in cursor.fetchall():
        lat, lon = float(lat), float(lon)

        # The town with the most addresses in the cell
        cell = (lat, lon)
        if count > fine_best.get(cell, 0):
            fine_best[cell] = count
            fine[cell] = town_id

        # Wider cells add up each town's addresses
        wide = (round(lat, 1), round(lon, 1))
        totals = coarse_totals.setdefault(wide, {})
        totals[town_id] = totals.get(town_id, 0) + count

    # The town with the most addresses in the wide cell
    for wide, totals in coarse_totals.items():
        coarse[wide] = max(totals, key=totals.get)

    return fine, coarse


def find_town(lat: float, lon: float, fine: dict, coarse: dict) -> int | None:
    """Returns the town at a coordinate.

    Args:
        lat: The point's latitude.
        lon: The point's longitude.
        fine: Town id by coordinate rounded to two decimals.
        coarse: Town id by coordinate rounded to one decimal.

    Returns:
        The town id, or None where no addresses are mapped.
    """
    # Try the small square first
    cell = (round(lat, 2), round(lon, 2))
    if cell in fine:
        return fine[cell]

    # Then the wider one
    return coarse.get((round(lat, 1), round(lon, 1)))


def street_address(row: dict) -> str | None:
    """Builds the line shown under a place's name.

    Args:
        row: One scraped line from places.jsonl.

    Returns:
        "The number and street, the street, or None."
    """
    street = row.get("street")
    if not street:
        return None
    number = row.get("number")
    return f"{number} {street}" if number else street


def fullness(row: dict) -> tuple[int, int]:
    """Scores how complete a place row is.

    Args:
        row: One scraped line from places.jsonl.

    Returns:
        (has an address, is an outline).
    """
    # An address outranks an outline
    has_address = 1 if row.get("street") else 0
    is_outline = 0 if row["osm_id"].startswith("node:") else 1
    return has_address, is_outline


print("Loading places")

connection = connect()
with connection.cursor() as cursor:
    fine, coarse = build_grid(cursor)
    print(f"  town grid: {len(fine):,} cells")

    # One place per name and spot
    best = {}
    with PLACES_PATH.open(encoding="utf-8") as places_file:
        for line in places_file:
            row = json.loads(line)

            # Key of name, lat and lon
            key = (row["name"].lower(), round(row["lat"], 3), round(row["lon"], 3))

            # The first copy, or replace with the fuller one
            if key not in best or fullness(row) > fullness(best[key]):
                best[key] = row

    # Town ids by name
    cursor.execute("SELECT lower(display), id FROM towns;")
    town_ids = dict(cursor.fetchall())

    rows = []
    for row in best.values():
        # Find town id though name, or its coordinates
        town_id = town_ids.get((row.get("town") or "").lower())
        if town_id is None:
            town_id = find_town(row["lat"], row["lon"], fine, coarse)

        # Categorize
        category = row["category"]
        if category in TOWN_CATEGORIES:
            kind = "town"
        elif category in NEIGHBOURHOOD_CATEGORIES:
            kind = "neighborhood"
        else:
            kind = "place"
        address = street_address(row)

        # A row for the main name and every nickname
        searchable = [(f"osm:{row['osm_id']}", row["name"])]
        for index, alternate in enumerate(row["alternates"]):
            searchable.append((f"osm:{row['osm_id']}:{index}", alternate))

        for place_id, search_name in searchable:
            rows.append(
                (
                    place_id,
                    kind,
                    category,
                    normalize_street(search_name),
                    row["name"],
                    address,
                    None,
                    town_id,
                    row["lat"],
                    row["lon"],
                    row["notable"],
                    "osm",
                )
            )
    print(f"  {len(rows):,} rows from OSM")

    # MBTA stations from GTFS
    stations = 0
    with STOPS_PATH.open(encoding="utf-8-sig", newline="") as stops_file:
        for stop in csv.DictReader(stops_file):
            # Stations only, not platforms
            if stop["location_type"] != "1":
                continue

            lat, lon = float(stop["stop_lat"]), float(stop["stop_lon"])
            rows.append(
                (
                    f"station:{stop['stop_id']}",
                    "station",
                    None,
                    normalize_street(stop["stop_name"]),
                    stop["stop_name"],
                    None,
                    stop["stop_id"],
                    find_town(lat, lon, fine, coarse),
                    lat,
                    lon,
                    False,
                    "gtfs",
                )
            )
            stations += 1
    print(f"  {stations} stations")

    # Village names from the address data
    cursor.execute(STREET_NEIGHBORHOODS)
    villages = 0
    for neighborhood, town_id, lat, lon in cursor.fetchall():
        rows.append(
            (
                f"village:{town_id}:{neighborhood.lower()}",
                "neighborhood",
                None,
                normalize_street(neighborhood),
                neighborhood,
                None,
                None,
                town_id,
                float(lat),
                float(lon),
                False,
                "massgis",
            )
        )
        villages += 1
    print(f"  {villages} village names")

    # One transaction for every source
    cursor.execute("TRUNCATE places;")
    cursor.executemany(INSERT_PLACE, rows)
connection.commit()

print(f"Loaded {len(rows):,} places")
