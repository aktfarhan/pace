"""Scrape Massachusetts address points into data/raw/addresses/."""

import json
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent.parent
OUT_DIR = ROOT / "data" / "raw" / "addresses"

# MassGIS statewide points, Boston from the city's SAM
MASSGIS_URL = (
    "https://arcgisserver.digital.mass.gov/arcgisserver/rest/services"
    "/AGOL/MassGIS_Master_Address_Points/MapServer/0/query"
)
BOSTON_URL = (
    "https://gisportal.boston.gov/arcgis/rest/services"
    "/SAM/Live_SAM_Address/FeatureServer/0/query"
)

# Boston's TOWN_ID in MassGIS
BOSTON_TOWN_ID = 35

PAGE_SIZE = 2000

# Grab the main elements; OBJECTID marks where a page ended
MASSGIS_FIELDS = (
    "OBJECTID,ADDRESS_NUMBER,FULL_NUMBER_STANDARDIZED,STREET_NAME,"
    "GEOGRAPHIC_TOWN_ID,GEOGRAPHIC_TOWN,COMMUNITY_NAME,PC_NAME"
)
BOSTON_FIELDS = (
    "OBJECTID,STREET_NUMBER,STREET_NUMBER_SORT,FULL_STREET_NAME,MAILING_NEIGHBORHOOD"
)


def fetch_pages(
    client: httpx.Client, url: str, where: str, fields: str, out_path: Path
) -> int:
    """Pages one address service into a JSONL file.

    Args:
        client: An open httpx client.
        url: The service's query endpoint.
        where: Which rows to keep.
        fields: The columns to request.
        out_path: The file the rows are added to.

    Returns:
        The row count in the finished file.
    """
    # Rows an earlier run already wrote
    written = 0
    last_line = ""
    if out_path.exists():
        with out_path.open(encoding="utf-8") as existing_file:
            for line in existing_file:
                written += 1
                last_line = line

    # How many rows the service has
    response = client.get(
        url, params={"where": where, "returnCountOnly": "true", "f": "json"}
    )
    response.raise_for_status()
    total = response.json()["count"]

    # Break if already have all data
    if written >= total:
        print(f"  {out_path.name}: already complete ({written:,} rows)")
        return written

    # The id the last run stopped on
    last_id = json.loads(last_line)["OBJECTID"] if last_line else 0

    with out_path.open("a", encoding="utf-8", newline="\n") as out_file:
        while written < total:
            # Each page starts after the last id
            response = client.get(
                url,
                params={
                    "where": f"{where} AND OBJECTID > {last_id}",
                    "outFields": fields,
                    "outSR": 4326,
                    "orderByFields": "OBJECTID",
                    "resultRecordCount": PAGE_SIZE,
                    "f": "json",
                },
            )
            response.raise_for_status()
            features = response.json()["features"]

            # An empty page
            if not features:
                break

            # Turn the point into the row for JSONL
            for feature in features:
                row = feature["attributes"]
                geometry = feature.get("geometry")
                if geometry:
                    row["lon"] = geometry["x"]
                    row["lat"] = geometry["y"]
                out_file.write(json.dumps(row) + "\n")
            written += len(features)
            last_id = features[-1]["attributes"]["OBJECTID"]

            # Progress every 50 pages
            if (written // PAGE_SIZE) % 50 == 0:
                print(f"  {out_path.name}: {written:,} / {total:,}")

    print(f"  {out_path.name}: {written:,} rows")
    return written


OUT_DIR.mkdir(parents=True, exist_ok=True)
print(f"Scraping address points -> {OUT_DIR}")

with httpx.Client(timeout=60) as client:
    state_rows = fetch_pages(
        client,
        MASSGIS_URL,
        f"GEOGRAPHIC_TOWN_ID <> {BOSTON_TOWN_ID}",
        MASSGIS_FIELDS,
        OUT_DIR / "massgis.jsonl",
    )
    boston_rows = fetch_pages(
        client,
        BOSTON_URL,
        "1=1",
        BOSTON_FIELDS,
        OUT_DIR / "boston.jsonl",
    )

print(f"Saved {state_rows:,} state rows + {boston_rows:,} Boston rows to {OUT_DIR}")
