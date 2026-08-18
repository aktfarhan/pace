"""Fetch live MBTA alerts for the routes and stations named in a query."""

import sys
from datetime import datetime, timezone

import httpx

from backend.mbta import fetch
from backend.retrieve import Row, match_route_ids, match_station_ids
from data.schema import connect

# System-wide fetches keep the biggest alerts only
TOP_ALERTS = 8

# Effects that leave a stop with nothing to board
SERVICE_EFFECTS = {
    "SUSPENSION",
    "NO_SERVICE",
    "CANCELLATION",
    "STATION_CLOSURE",
    "STOP_CLOSURE",
    "STOP_MOVE",
    "SHUTTLE",
}


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


def fetch_alerts(
    query: str, route: str | None = None, when: str | None = None
) -> list[Row]:
    """Fetches the alerts for whatever the query names.

    Args:
        query: The user's question.
        route: The classifiers route read.
        when: An ISO moment to ask about.

    Returns:
        Alert rows shaped like retrieved chunks. Zero alerts returns one
        no-active-alerts row so the answer can cite it.
    """
    # Match the routes and stations the query names
    connection = connect()
    with connection.cursor() as cursor:
        route_ids = match_route_ids(cursor, route) if route else []
        station_ids = match_station_ids(cursor, query)

    # Stations get accessibility alerts also
    params = {"filter[datetime]": when or "NOW"}
    if station_ids:
        stop_ids = [chunk_id.removeprefix("stop:") for chunk_id in station_ids]
        params["filter[stop]"] = ",".join(stop_ids)
        params["filter[activity]"] = "ALL"
    if route_ids:
        params["filter[route]"] = ",".join(route_ids)

    # Fetch the active alerts
    alerts = fetch("/alerts", params)["data"]
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
        text = f"No active alerts for {subject} as of {when or retrieved_at}."
        return [("alert:none", "alert", text, {"retrieved_at": retrieved_at}, 0.0)]

    # Shape each alert like a retrieved chunk
    rows = []
    for alert in alerts:
        rows.append(render_alert(alert, retrieved_at))
    return rows


def blocking_alerts(query: str, route: str | None, when: str | None) -> list[Row]:
    """Fetches the alerts that explain why nothing is scheduled.

    Args:
        query: The user's question.
        route: The classifiers route read.
        when: An ISO moment to ask about.

    Returns:
        Alert rows whose effect leaves nothing to board.
    """
    try:
        alerts = fetch_alerts(query, route, when)
    except httpx.HTTPError:
        return []

    # Keep the alerts that stop service
    stopping = []
    for row in alerts:
        _, _, _, metadata, _ = row
        if metadata.get("effect") in SERVICE_EFFECTS:
            stopping.append(row)
    return stopping


if __name__ == "__main__":
    query = sys.argv[1]
    for chunk_id, kind, text, metadata, distance in fetch_alerts(query):
        print(f"{chunk_id} {text[:100]}")
