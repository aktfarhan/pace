"""Scrape named places from the Massachusetts OpenStreetMap."""

import json
from pathlib import Path

import httpx
import osmium

from data.places.normalize import normalize_street

ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DIR = ROOT / "data" / "raw" / "places"
EXTRACT_PATH = RAW_DIR / "massachusetts-latest.osm.pbf"
OUT_PATH = RAW_DIR / "places.jsonl"

EXTRACT_URL = (
    "https://download.geofabrik.de/north-america/us/massachusetts-latest.osm.pbf"
)

# Keys
CATEGORY_KEYS = (
    "amenity",
    "shop",
    "leisure",
    "tourism",
    "healthcare",
    "office",
    "historic",
    "craft",
    "aeroway",
    "natural",
    "building",
)

# Non destinations
SKIP_CATEGORIES = {
    "bench",
    "bicycle_parking",
    "camp_pitch",
    "drinking_water",
    "fountain",
    "information",
    "parking_space",
    "pitch",
    "post_box",
    "recycling",
    "shelter",
    "street_lamp",
    "surveillance",
    "telephone",
    "toilets",
    "vending_machine",
    "waste_basket",
    "waste_disposal",
}

# Named places
PLACE_CATEGORIES = {
    "neighbourhood",
    "suburb",
    "quarter",
    "borough",
    "hamlet",
    "town",
    "city",
    "village",
    "square",
}

# Tags holding the other names a place goes by
ALTERNATE_KEYS = ("short_name", "alt_name", "official_name")


def download_extract() -> None:
    """Downloads the Massachusetts extract when it is not already on disk."""
    # Check if the file already exists
    if EXTRACT_PATH.exists():
        size = EXTRACT_PATH.stat().st_size / 1_000_000
        print(f"  {EXTRACT_PATH.name}: already downloaded ({size:,.0f} MB)")
        return

    print(f"  downloading {EXTRACT_URL.rsplit('/', 1)[-1]}")

    # Download the file
    with httpx.stream("GET", EXTRACT_URL, follow_redirects=True, timeout=120) as source:
        source.raise_for_status()
        total = int(source.headers.get("content-length", 0))

        written = 0
        with EXTRACT_PATH.open("wb") as extract_file:
            for block in source.iter_bytes(chunk_size=1_000_000):
                extract_file.write(block)
                written += len(block)

                # Progress every 50 MB
                if written % 50_000_000 < 1_000_000:
                    done = written / 1_000_000
                    print(f"    {done:,.0f} / {total / 1_000_000:,.0f} MB")

    print(f"  {EXTRACT_PATH.name}: {written / 1_000_000:,.0f} MB")


def category(tags) -> str | None:
    """Returns the kind of place a feature is, or None.

    Args:
        tags: An OSM object's tags.

    Returns:
        The value of the first category tag or None.
    """
    # The first key the feature has
    for key in CATEGORY_KEYS:
        value = tags.get(key)
        if value and value not in SKIP_CATEGORIES:
            return key if value == "yes" else value

    # Neighbourhoods
    place = tags.get("place")
    if place in PLACE_CATEGORIES:
        return place
    return None


def alternates(tags, name: str) -> list[str]:
    """Collects the other names a place goes by.

    Args:
        tags: An OSM object's tags.
        name: The feature's main name.

    Returns:
        The other names, without the main or repeats.
    """
    names = []

    # Names already covered
    seen = {normalize_street(name)}

    for key in ALTERNATE_KEYS:
        value = tags.get(key)
        if not value:
            continue

        # Find and add alternate names to names
        for part in value.split(";"):
            part = part.strip()
            if not part:
                continue

            # Check if same name
            shaped = normalize_street(part)
            if shaped not in seen:
                seen.add(shaped)
                names.append(part)
    return names


def centroid(area) -> tuple[float, float] | None:
    """Averages the corner positions of an area's outer rings.

    Args:
        area: An assembled OSM area.

    Returns:
        (lat, lon) at the middle of the outline, or None.
    """
    # The running totals for the average
    lat_sum = 0.0
    lon_sum = 0.0
    count = 0

    # Add up every corner of every outline
    for ring in area.outer_rings():
        for node in ring:
            lat_sum += node.location.lat
            lon_sum += node.location.lon
            count += 1

    # Make sure there are corners
    if not count:
        return None

    # The middle of the corners
    return lat_sum / count, lon_sum / count


RAW_DIR.mkdir(parents=True, exist_ok=True)
print(f"Scraping places -> {RAW_DIR}")
download_extract()

# Ways and relations are read to build areas
entities = osmium.osm.NODE | osmium.osm.WAY | osmium.osm.RELATION
processor = osmium.FileProcessor(EXTRACT_PATH, entities).with_areas()

kept = 0
with OUT_PATH.open("w", encoding="utf-8", newline="\n") as out_file:
    for feature in processor:
        # Make sure it's a real name
        name = (feature.tags.get("name") or "").strip()
        if len(name) < 3 or name.isdigit():
            continue

        # Check if it is a destination
        kind = category(feature.tags)
        if not kind:
            continue

        # Node carries its own position
        if feature.is_node():
            osm_id = f"node:{feature.id}"
            point = (feature.location.lat, feature.location.lon)

        # Area needs the centroid
        elif feature.is_area():
            source = "way" if feature.from_way() else "relation"
            osm_id = f"{source}:{feature.orig_id()}"
            point = centroid(feature)
        else:
            continue

        if point is None:
            continue

        row = {
            "osm_id": osm_id,
            "name": name,
            "alternates": alternates(feature.tags, name),
            "category": kind,
            "lat": point[0],
            "lon": point[1],
            "street": feature.tags.get("addr:street"),
            "number": feature.tags.get("addr:housenumber"),
            "town": feature.tags.get("addr:city"),
            "notable": feature.tags.get("wikipedia") is not None,
        }
        out_file.write(json.dumps(row, ensure_ascii=False) + "\n")
        kept += 1

        # Progress every 25k places
        if kept % 25_000 == 0:
            print(f"  {kept:,} places")

print(f"Saved {kept:,} places to {OUT_PATH}")
