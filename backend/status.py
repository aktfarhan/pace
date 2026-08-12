"""Read the system alert feed and reduce it to one state per rail line."""

import json
import re
from datetime import datetime, timezone
from typing import Any, Literal, TypedDict

import httpx

from backend.mbta import fetch

# Heavy rail, light rail, and commuter rail
RAIL_TYPES = "0,1,2"

# The activities that count as riding
RIDING_ACTIVITIES = "BOARD,EXIT,RIDE"

# The rail lines the sidebar draws, in board order
LINES: list[tuple[str, str, str]] = [
    ("Red", "RED", "Red Line"),
    ("Orange", "ORANGE", "Orange Line"),
    ("Green", "GREEN", "Green Line"),
    ("Blue", "BLUE", "Blue Line"),
    ("CR", "COMMUTER", "Commuter Rail"),
]

# Worst effect first
EFFECT_ORDER = {
    "SUSPENSION": 0,
    "NO_SERVICE": 1,
    "CANCELLATION": 2,
    "SHUTTLE": 3,
    "STATION_CLOSURE": 4,
    "DETOUR": 5,
    "DELAY": 6,
    "TRACK_CHANGE": 7,
    "SERVICE_CHANGE": 8,
    "STOP_MOVE": 9,
    "STOP_CLOSURE": 10,
    "STATION_ISSUE": 11,
}
UNRANKED = len(EFFECT_ORDER)

SEVERE_EFFECTS = {"SUSPENSION", "NO_SERVICE", "CANCELLATION"}
DISRUPTED_EFFECTS = {"SHUTTLE", "DETOUR", "DELAY"}

# The delay number in an alert's header
DELAY_MINUTES = re.compile(r"delays of about (\d+) minutes")

State = Literal["clear", "notice", "disrupted", "severe"]


class LineStatus(TypedDict):
    """One line's card in the rail."""

    line_id: str
    badge_text: str
    line_name: str
    state: State
    effect: str | None
    cause: str | None
    headline: str | None
    alert_delay_minutes: int | None
    since: str | None
    until: str | None
    branch_ids: list[str]
    directions: list[int]
    stop_count: int
    alert_count: int


class SystemStatus(TypedDict):
    """Every rail line's state at one moment."""

    lines: list[LineStatus]
    clear_count: int
    retrieved_at: str
    ok: bool


def fetch_rail_alerts() -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Fetches the alerts in effect on the rail lines.

    Returns:
        Tuple of (alerts, route_id -> route_type).
    """
    params = {
        "filter[datetime]": "NOW",
        "filter[route_type]": RAIL_TYPES,
        "filter[activity]": RIDING_ACTIVITIES,
        "include": "routes",
    }
    payload = fetch("/alerts", params)

    # Build each route's GTFS type
    route_types = {}
    for record in payload.get("included", []):
        route_types[record["id"]] = record["attributes"]["type"]
    return payload["data"], route_types


def line_of(route_id: str, route_types: dict[str, int]) -> str | None:
    """Returns the sidebar line a route belongs to.

    Args:
        route_id: An MBTA route id.
        route_types: route_id -> GTFS route type.

    Returns:
        A line id, or None for a route the rail does not draw.
    """
    if route_types.get(route_id) == 2:
        return "CR"
    if route_id.startswith("Green-"):
        return "Green"
    if route_id in ("Red", "Orange", "Blue"):
        return route_id
    return None


def earliest_start(alert: dict[str, Any]) -> str | None:
    """Returns the moment an alert came into effect.

    Args:
        alert: An alert record.

    Returns:
        The earliest period start, or None.
    """
    starts = []
    for period in alert["attributes"]["active_period"]:
        if period["start"] is not None:
            starts.append(period["start"])
    if not starts:
        return None
    return min(starts)


def latest_end(alert: dict[str, Any]) -> str | None:
    """Returns the moment an alert stops being in effect.

    Args:
        alert: An alert record.

    Returns:
        The latest period end, or None when any period is open-ended.
    """
    ends = []
    for period in alert["attributes"]["active_period"]:
        if period["end"] is None:
            return None
        ends.append(period["end"])
    if not ends:
        return None
    return max(ends)


def delay_minutes(alert: dict[str, Any]) -> int | None:
    """Reads the delay number MBTA writes.

    Args:
        alert: An alert record.

    Returns:
        The minutes, or None when the header carries no figure.
    """
    attributes = alert["attributes"]
    if attributes["effect"] != "DELAY":
        return None

    found = DELAY_MINUTES.search(attributes["header"] or "")
    if found is None:
        return None
    return int(found.group(1))


def directions_of(alert: dict[str, Any]) -> list[int]:
    """Returns the directions of travel an alert names.

    Args:
        alert: An alert record.

    Returns:
        0, 1, or both, sorted.
    """
    directions = set()
    for entity in alert["attributes"]["informed_entity"]:
        if "direction_id" in entity:
            directions.add(entity["direction_id"])
    return sorted(directions)


def stops_of(alert: dict[str, Any]) -> int:
    """Counts the stops an alert names.

    Args:
        alert: An alert record.

    Returns:
        How many distinct stops it touches.
    """
    stops = set()
    for entity in alert["attributes"]["informed_entity"]:
        stops.add(entity["stop"])
    return len(stops)


def rank(alert: dict[str, Any]) -> tuple[int, int, str]:
    """Sorts an alert against the others on its line.

    Args:
        alert: An alert record.

    Returns:
        A key placing the worst effect first, then the highest severity,
        then the longest-running.
    """
    attributes = alert["attributes"]
    order = EFFECT_ORDER.get(attributes["effect"], UNRANKED)
    return (order, -attributes["severity"], earliest_start(alert) or "")


def state_of(effect: str) -> State:
    """Returns the card a line's worst effect earns.

    Args:
        effect: The line's worst effect.

    Returns:
        The state.
    """
    if effect in SEVERE_EFFECTS:
        return "severe"
    if effect in DISRUPTED_EFFECTS:
        return "disrupted"
    return "notice"


def read_line(
    line_id: str, badge_text: str, line_name: str, alerts: list[dict[str, Any]]
) -> LineStatus:
    """Reduces one line's alerts to the card it draws.

    Args:
        line_id: The sidebar line.
        badge_text: The badge's wording.
        line_name: The line's spoken name.
        alerts: Every alert on that line.

    Returns:
        The line's card.
    """
    if not alerts:
        return {
            "line_id": line_id,
            "badge_text": badge_text,
            "line_name": line_name,
            "state": "clear",
            "effect": None,
            "cause": None,
            "headline": None,
            "alert_delay_minutes": None,
            "since": None,
            "until": None,
            "branch_ids": [],
            "directions": [],
            "stop_count": 0,
            "alert_count": 0,
        }

    worst = min(alerts, key=rank)
    attributes = worst["attributes"]

    # Every route the worst alert names
    branches = set()
    for record in worst["relationships"]["routes"]["data"]:
        branches.add(record["id"])

    return {
        "line_id": line_id,
        "badge_text": badge_text,
        "line_name": line_name,
        "state": state_of(attributes["effect"]),
        "effect": attributes["effect"],
        "cause": attributes["cause"],
        "headline": attributes["service_effect"],
        "alert_delay_minutes": delay_minutes(worst),
        "since": earliest_start(worst),
        "until": latest_end(worst),
        "branch_ids": sorted(branches),
        "directions": directions_of(worst),
        "stop_count": stops_of(worst),
        "alert_count": len(alerts),
    }


def read_status() -> SystemStatus:
    """Reads every rail line's state from the live alert feed.

    Returns:
        One card per line in board order.
    """
    retrieved_at = datetime.now(timezone.utc).isoformat()
    try:
        alerts, route_types = fetch_rail_alerts()
    except httpx.HTTPError:
        lines = []
        for line_id, badge_text, line_name in LINES:
            lines.append(read_line(line_id, badge_text, line_name, []))
        return {
            "lines": lines,
            "clear_count": len(LINES),
            "retrieved_at": retrieved_at,
            "ok": False,
        }

    # One alert can name several routes on one line
    filed: dict[str, list[dict[str, Any]]] = {}
    for alert in alerts:
        seen = set()
        for record in alert["relationships"]["routes"]["data"]:
            line_id = line_of(record["id"], route_types)
            if line_id is not None and line_id not in seen:
                seen.add(line_id)
                filed.setdefault(line_id, []).append(alert)

    lines = []
    clear_count = 0
    for line_id, badge_text, line_name in LINES:
        line = read_line(line_id, badge_text, line_name, filed.get(line_id, []))
        if line["state"] == "clear":
            clear_count += 1
        lines.append(line)

    return {
        "lines": lines,
        "clear_count": clear_count,
        "retrieved_at": retrieved_at,
        "ok": True,
    }


if __name__ == "__main__":
    print(json.dumps(read_status(), indent=2))
