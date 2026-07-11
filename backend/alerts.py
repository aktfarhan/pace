"""Fetch live MBTA alerts for the routes and stations named in a query."""

import os
import re
import sys
from datetime import datetime, timezone

import httpx
import psycopg
from dotenv import load_dotenv

from backend.retrieve import Row, match_station_ids
from data.schema import connect

# Reads the .env
load_dotenv()

API_KEY = os.environ["MBTA_API_KEY"]
BASE_URL = "https://api-v3.mbta.com"

# System-wide fetches keep the biggest alerts only
TOP_ALERTS = 8

ROUTES = """
    SELECT metadata->>'route_id' AS route_id,
           metadata->>'long_name' AS long_name,
           metadata->>'short_name' AS short_name
    FROM chunks WHERE kind = 'route';
"""


def match_route_ids(cursor: psycopg.Cursor, query: str) -> list[str]:
    """Finds routes named in the query.

    Args:
        cursor: An open cursor on the database.
        query: The user's question.

    Returns:
        Route IDs whose long_name or short_name appears in the query.
        Slash names match by part. A trailing branch letter is dropped.
    """
    cursor.execute(ROUTES)
    matched = []
    lowered = query.lower()
    for route_id, long_name, short_name in cursor.fetchall():
        # Name phrases this route answers to
        phrases = long_name.lower().split("/")

        # Drop trailing branch letter so "green line" matches Green Line B
        first, _, last = long_name.lower().rpartition(" ")
        if first and len(last) == 1:
            phrases.append(first)

        # Bus short names ("1", "66")
        if short_name:
            phrases.append(short_name.lower())

        # Word-boundary match against the query
        for phrase in phrases:
            if re.search(rf"\b{re.escape(phrase)}\b", lowered):
                matched.append(route_id)
                break
    return matched


def render_alert(alert: dict, retrieved_at: str) -> Row:
    """Builds one alert row shaped like a retrieved chunk.

    Args:
        alert: An alert record from the MBTA API.
        retrieved_at: When the fetch happened.

    Returns:
        A (id, kind, text, metadata, distance) row. Text is MBTA's own
        service_effect and header + severity.
    """
    attributes = alert["attributes"]

    # MBTA's wording plus the severity
    text = (
        f"{attributes['service_effect']}. {attributes['header']} "
        f"Severity {attributes['severity']} of 10."
    )

    metadata = {
        "alert_id": alert["id"],
        "effect": attributes["effect"],
        "severity": attributes["severity"],
        "cause": attributes["cause"],
        "lifecycle": attributes["lifecycle"],
        "active_period": attributes["active_period"],
        "updated_at": attributes["updated_at"],
        "retrieved_at": retrieved_at,
    }
    return (f"alert:{alert['id']}", "alert", text, metadata, 0.0)


def fetch_alerts(query: str) -> list[Row]:
    """Fetches active alerts for whatever the query names.

    Args:
        query: The user's question.

    Returns:
        Alert rows shaped like retrieved chunks. Zero alerts returns one
        no-active-alerts row so the answer can cite it.
    """
    # Match the routes and stations the query names
    connection = connect()
    with connection.cursor() as cursor:
        route_ids = match_route_ids(cursor, query)
        station_ids = match_station_ids(cursor, query)

    # Stations get accessibility alerts also
    params = {"filter[datetime]": "NOW"}
    if station_ids:
        stop_ids = [chunk_id.removeprefix("stop:") for chunk_id in station_ids]
        params["filter[stop]"] = ",".join(stop_ids)
        params["filter[activity]"] = "ALL"
    if route_ids:
        params["filter[route]"] = ",".join(route_ids)

    # Fetch the active alerts
    response = httpx.get(
        f"{BASE_URL}/alerts", params=params, headers={"X-API-Key": API_KEY}
    )
    response.raise_for_status()
    alerts = response.json()["data"]
    retrieved_at = datetime.now(timezone.utc).isoformat()

    # Keep big alerts for system-wide
    if not station_ids and not route_ids:
        alerts.sort(key=lambda alert: alert["attributes"]["severity"], reverse=True)
        alerts = alerts[:TOP_ALERTS]

    # Zero alerts case
    if not alerts:
        if route_ids:
            subject = ", ".join(route_ids)
        elif station_ids:
            subject = "this station"
        else:
            subject = "the MBTA system"
        text = f"No active alerts for {subject} as of {retrieved_at}."
        return [("alert:none", "alert", text, {"retrieved_at": retrieved_at}, 0.0)]

    # Shape each alert like a retrieved chunk
    rows = []
    for alert in alerts:
        rows.append(render_alert(alert, retrieved_at))
    return rows


if __name__ == "__main__":
    query = sys.argv[1]
    for chunk_id, kind, text, metadata, distance in fetch_alerts(query):
        print(f"{chunk_id} {text[:100]}")
