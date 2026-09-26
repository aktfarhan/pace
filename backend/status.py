"""Read the system alert feed and reduce it to one state per rail line."""

import json
import re
from datetime import datetime, timezone
from typing import Literal, TypedDict

import httpx

from backend.lines import LINES, LINE_OF
from backend.mbta import Alert, fetch
from backend.timetable import gtfs_stamp, load_routes, load_stops

# Heavy rail, light rail, and commuter rail
RAIL_TYPES = "0,1,2"

# A station id, as against a door
STATION_PREFIX = "place-"

# What narrows an alert below its whole mode
NARROWING = {"stop", "trip", "facility"}

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

# The effects that hold a train up
SLOWING_EFFECTS = SEVERE_EFFECTS | DISRUPTED_EFFECTS

# Alerts that leave the trains running
ACCESS_EFFECTS = {
    "ELEVATOR_CLOSURE",
    "ESCALATOR_CLOSURE",
    "ACCESS_ISSUE",
    "PARKING_ISSUE",
}

# The phrasings a delay number comes in
DELAY_FIGURES = (
    re.compile(r"(\d+)(?:[-–](\d+))? minutes behind schedule", re.IGNORECASE),
    re.compile(r"delays of about (\d+)(?:[-–](\d+))? minutes", re.IGNORECASE),
)

State = Literal["clear", "notice", "disrupted", "severe"]


class LineAlert(TypedDict):
    """One alert in effect on a line."""

    alert_id: str
    effect: str
    headline: str
    detail: str
    since: str | None
    until: str | None
    slowing: bool
    where: str | None
    spread: int


class LineStatus(TypedDict):
    """One line's card in the rail."""

    line_id: str
    badge_text: str
    line_name: str
    state: State
    effect: str | None
    cause: str | None
    headline: str | None
    alert_delay_minutes: tuple[int, int] | None
    since: str | None
    until: str | None
    branch_ids: list[str]
    directions: list[int]
    stop_count: int
    alert_count: int
    alerts: list[LineAlert]


class SystemStatus(TypedDict):
    """Every rail line's state at one moment."""

    lines: list[LineStatus]
    clear_count: int
    retrieved_at: str
    ok: bool


def fetch_rail_alerts() -> list[Alert]:
    """Fetches the alerts in effect on the rail lines.

    Returns:
        The alerts in effect.
    """
    params = {
        "filter[datetime]": "NOW",
        "filter[route_type]": RAIL_TYPES,
        "filter[activity]": "ALL",
    }
    return fetch("/alerts", params)["data"]


def earliest_start(alert: Alert) -> str | None:
    """Returns the moment an alert came into effect.

    Args:
        alert: An alert record.

    Returns:
        The earliest period start, or None.
    """
    starts = []
    for period in alert["attributes"]["active_period"]:
        starts.append(period["start"])
    if not starts:
        return None
    return min(starts)


def latest_end(alert: Alert) -> str | None:
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


def delay_minutes(alert: Alert) -> tuple[int, int] | None:
    """Reads the delay number MBTA writes.

    Args:
        alert: An alert record.

    Returns:
        The fewest and most minutes, equal when the header names one number.
    """
    attributes = alert["attributes"]
    if attributes["effect"] != "DELAY":
        return None

    # The first phrasing that matches carries the number
    for pattern in DELAY_FIGURES:
        found = pattern.search(attributes["header"])
        if found is not None:
            spread = found.group(2)
            fewest = int(found.group(1))
            most = fewest if spread is None else int(spread)
            return (fewest, most)
    return None


def routes_of(alert: Alert) -> set[str]:
    """Names the routes an alert covers.

    Args:
        alert: An alert record.

    Returns:
        The route ids.
    """
    labels = load_routes(gtfs_stamp())

    routes = set()
    for entity in alert["attributes"]["informed_entity"]:
        if "route" in entity:
            routes.add(entity["route"])
            continue

        if entity.keys() & NARROWING:
            continue

        # Only a whole mode covers every route
        for route, (_, _, mode) in labels.items():
            if route in LINE_OF and mode == entity.get("route_type"):
                routes.add(route)
    return routes


def directions_of(alert: Alert) -> list[int]:
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


def stops_of(alert: Alert) -> int:
    """Counts the stops an alert names.

    Args:
        alert: An alert record.

    Returns:
        How many distinct stops it touches.
    """
    stops = set()
    for entity in alert["attributes"]["informed_entity"]:
        if "stop" in entity:
            stops.add(entity["stop"])
    return len(stops)


def rank(alert: Alert) -> tuple[int, int, str]:
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


def stations_of(alert: Alert) -> set[str]:
    """Names the stations an alert touches.

    Args:
        alert: An alert record.

    Returns:
        The station names.
    """
    names, _, parents, _ = load_stops(gtfs_stamp())

    # A platform counts under its station
    touched: set[str] = set()
    for entity in alert["attributes"]["informed_entity"]:
        stop = entity.get("stop")
        if not stop:
            continue

        touched.add(parents.get(stop, stop))

    # A named station
    stations: set[str] = set()
    for stop in touched:
        if stop.startswith(STATION_PREFIX):
            stations.add(stop)

    named: set[str] = set()
    for stop in stations or touched:
        if stop in names:
            named.add(names[stop])

    return named


def where_of(stations: set[str]) -> str | None:
    """Names the station an alert is about.

    Args:
        stations: The stations it touches.

    Returns:
        The station's name, or None.
    """
    if len(stations) != 1:
        return None

    return next(iter(stations))


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


def render_line_alert(alert: Alert) -> LineAlert:
    """Shapes one alert the way the transit page reads it.

    Args:
        alert: An alert record.

    Returns:
        The alert's own row.
    """
    attributes = alert["attributes"]
    stations = stations_of(alert)
    return {
        "alert_id": alert["id"],
        "effect": attributes["effect"],
        "headline": attributes["service_effect"],
        "detail": attributes["header"],
        "since": earliest_start(alert),
        "until": latest_end(alert),
        "slowing": attributes["effect"] in SLOWING_EFFECTS,
        "where": where_of(stations),
        "spread": len(stations),
    }


def read_line(
    line_id: str, badge_text: str, line_name: str, alerts: list[Alert]
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
    # Station and accessibility alerts do not disrupt the train
    scored = []
    for alert in alerts:
        if alert["attributes"]["effect"] not in ACCESS_EFFECTS:
            scored.append(alert)

    # Worst first, whether or not it counts against the line
    listed = []
    for alert in sorted(alerts, key=rank):
        listed.append(render_line_alert(alert))

    if not scored:
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
            "alerts": listed,
        }

    worst = min(scored, key=rank)
    attributes = worst["attributes"]

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
        "branch_ids": sorted(routes_of(worst)),
        "directions": directions_of(worst),
        "stop_count": stops_of(worst),
        "alert_count": len(scored),
        "alerts": listed,
    }


def without_alerts(live: SystemStatus) -> SystemStatus:
    """Drops the alert lists a caller did not ask for.

    Args:
        live: One reading of the system.

    Returns:
        The same reading with every line's alert list emptied.
    """
    lines = []
    for line in live["lines"]:
        lines.append({**line, "alerts": []})
    return {**live, "lines": lines}


def read_status() -> SystemStatus:
    """Reads every rail line's state from the live alert feed.

    Returns:
        One card per line in board order.
    """
    retrieved_at = datetime.now(timezone.utc).isoformat()
    try:
        alerts = fetch_rail_alerts()
    except httpx.HTTPError:
        lines = []
        for line_id, badge_text, line_name, _ in LINES:
            lines.append(read_line(line_id, badge_text, line_name, []))
        return {
            "lines": lines,
            "clear_count": len(LINES),
            "retrieved_at": retrieved_at,
            "ok": False,
        }

    # One alert can name several routes on one line
    filed: dict[str, list[Alert]] = {}
    for alert in alerts:
        seen = set()
        for route in routes_of(alert):
            line_id = LINE_OF.get(route)
            if line_id is not None and line_id not in seen:
                seen.add(line_id)
                filed.setdefault(line_id, []).append(alert)

    lines = []
    clear_count = 0
    for line_id, badge_text, line_name, _ in LINES:
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
