"""Load scraped address points into the towns, streets, and address_points tables."""

import json
from collections.abc import Callable, Iterator
from pathlib import Path

from data.places.normalize import normalize_street, title_case
from data.schema import connect

ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DIR = ROOT / "data" / "raw" / "addresses"

# Boston's town id and name
BOSTON_TOWN_ID = 35
BOSTON_TOWN = "Boston"

UPSERT_TOWN = """
    INSERT INTO towns (id, name, display) VALUES (%s, %s, %s)
    ON CONFLICT (id) DO UPDATE
    SET name = EXCLUDED.name, display = EXCLUDED.display;
"""
INSERT_STREET = """
    INSERT INTO streets (id, name, display, town_id, neighborhood, lat, lon, points)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
"""
CREATE_STAGING = """
    CREATE TEMP TABLE staging (
        street_id   integer,
        number_text text,
        number      integer,
        lat         double precision,
        lon         double precision
    );
"""

# One row per house number
FILL_POINTS = """
    INSERT INTO address_points (street_id, number_text, number, lat, lon)
    SELECT DISTINCT ON (street_id, number_text) street_id, number_text, number, lat, lon
    FROM staging ORDER BY street_id, number_text;
"""


def parse_massgis(row: dict) -> tuple | None:
    """Reads one MassGIS row.

    Args:
        row: One scraped line from massgis.jsonl.

    Returns:
        (town_id, town, street, neighborhood, number_text,
        number, lat, lon), or None.
    """
    lat = row.get("lat")
    lon = row.get("lon")
    street = row.get("STREET_NAME")
    town = row.get("GEOGRAPHIC_TOWN")
    number = row.get("ADDRESS_NUMBER")
    town_id = row.get("GEOGRAPHIC_TOWN_ID")
    number_text = row.get("FULL_NUMBER_STANDARDIZED")

    if not (number and number_text and street and town_id and town and lat and lon):
        return None

    # The postal name
    postal = row.get("PC_NAME")
    neighborhood = title_case(postal) if postal and postal != town else None
    return (
        town_id,
        title_case(town),
        title_case(street),
        neighborhood,
        number_text,
        number,
        lat,
        lon,
    )


def parse_boston(row: dict) -> tuple | None:
    """Reads one Boston SAM row.

    Args:
        row: One scraped line from boston.jsonl.

    Returns:
        (town_id, town, street, neighborhood, number_text,
        number, lat, lon), or None.
    """
    lat = row.get("lat")
    lon = row.get("lon")
    street = row.get("FULL_STREET_NAME")
    number = row.get("STREET_NUMBER_SORT")
    number_text = row.get("STREET_NUMBER")

    if not (number and number_text and street and lat and lon):
        return None

    # Downtown mails as "Boston"
    mailing = row.get("MAILING_NEIGHBORHOOD")
    neighborhood = mailing if mailing and mailing != BOSTON_TOWN else None
    return (
        BOSTON_TOWN_ID,
        BOSTON_TOWN,
        street,
        neighborhood,
        number_text,
        number,
        lat,
        lon,
    )


def read_addresses(
    path: Path, parse: Callable[[dict], tuple | None]
) -> Iterator[tuple]:
    """Reads a scraped file one row at a time.

    Args:
        path: The scraped JSONL file.
        parse: The reader for that file's source.

    Yields:
        One parsed row per line.
    """
    # Yield one row at a time
    with path.open(encoding="utf-8") as address_file:
        for line in address_file:
            row = parse(json.loads(line))
            if row:
                yield row


SOURCES = [("massgis.jsonl", parse_massgis), ("boston.jsonl", parse_boston)]

print("Loading addresses")

connection = connect()
with connection.cursor() as cursor:
    cursor.execute(CREATE_STAGING)

    # Towns and streets, with every point copied
    town_names = {}
    streets = {}
    copy_sql = "COPY staging (street_id, number_text, number, lat, lon) FROM STDIN"
    with cursor.copy(copy_sql) as copy:
        for filename, parse in SOURCES:
            for row in read_addresses(RAW_DIR / filename, parse):
                town_id, town, street, neighborhood, number_text, number, lat, lon = row

                # A few rows carry a neighbour's town name
                seen = town_names.setdefault(town_id, {})
                seen[town] = seen.get(town, 0) + 1

                # A street is its name in one town, split by neighborhood
                key = (town_id, normalize_street(street), neighborhood)
                if key not in streets:
                    streets[key] = {
                        "id": len(streets) + 1,
                        "display": street,
                        "lat_sum": 0.0,
                        "lon_sum": 0.0,
                        "points": 0,
                    }

                # The running total for the center of the street
                streets[key]["lat_sum"] += lat
                streets[key]["lon_sum"] += lon
                streets[key]["points"] += 1
                copy.write_row((streets[key]["id"], number_text, number, lat, lon))

    print(f"  {len(town_names)} towns, {len(streets):,} streets")

    # Streets and points rebuild from scratch
    cursor.execute("TRUNCATE address_points, streets;")
    for town_id, seen in sorted(town_names.items()):
        town = max(seen, key=seen.get)
        cursor.execute(UPSERT_TOWN, (town_id, town.lower(), town))

    # The center is the middle of the street's own points
    street_rows = []
    for (town_id, name, neighborhood), street in streets.items():
        street_rows.append(
            (
                street["id"],
                name,
                street["display"],
                town_id,
                neighborhood,
                street["lat_sum"] / street["points"],
                street["lon_sum"] / street["points"],
                street["points"],
            )
        )
    cursor.executemany(INSERT_STREET, street_rows)
    cursor.execute(FILL_POINTS)

    cursor.execute("SELECT count(*) FROM address_points;")
    point_count = cursor.fetchone()[0]
connection.commit()

print(
    f"Loaded {len(town_names)} towns, {len(streets):,} streets, {point_count:,} points"
)
