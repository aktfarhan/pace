"""Fetch live departure predictions and scheduled times for the stops named in a query."""

import os
import re
import sys
from datetime import date, datetime, timedelta, timezone

import httpx
from dotenv import load_dotenv

from backend.retrieve import Row, match_route_ids, match_station_ids
from data.schema import connect

# Reads the .env
load_dotenv()

API_KEY = os.environ["MBTA_API_KEY"]
BASE_URL = "https://api-v3.mbta.com"

# Upcoming departures shown per route and direction
NEXT_DEPARTURES = 3

# Before this hour, "today" is still yesterday's MBTA service day
SERVICE_ROLLOVER_HOUR = 3

WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

ROUTE_INFO = """
    SELECT metadata->>'route_id' AS route_id,
           metadata->>'short_name' AS short_name,
           metadata->>'long_name' AS long_name,
           metadata->>'type' AS route_type,
           metadata->'direction_destinations' AS direction_destinations
    FROM chunks WHERE kind = 'route';
"""
STATION_NAMES = """
    SELECT id, metadata->>'name' AS name
    FROM chunks WHERE id = ANY(%s);
"""


def fetch(path: str, params: dict) -> list[dict]:
    """Returns the data rows for one MBTA API call.

    Args:
        path: The endpoint ("/predictions" or "/schedules").
        params: Query parameters for the call.

    Returns:
        The response's data list.
    """
    response = httpx.get(
        f"{BASE_URL}{path}", params=params, headers={"X-API-Key": API_KEY}
    )
    response.raise_for_status()
    return response.json()["data"]


def service_day(now: datetime) -> tuple[str, str]:
    """Returns the MBTA service date and clock time for a local moment.

    Args:
        now: The local time of the query.

    Returns:
        Tuple of (date "YYYY-MM-DD", time "HH:MM"). Before 3 AM the
        service day is still yesterday and hours count past 24, so a
        12:40 AM query asks for yesterday's date at 24:40.
    """
    # Past midnight the service clock keeps counting: 12:40 AM is 24:40
    if now.hour < SERVICE_ROLLOVER_HOUR:
        yesterday = now.date() - timedelta(days=1)
        return yesterday.isoformat(), f"{now.hour + 24}:{now.minute:02d}"
    return now.date().isoformat(), f"{now.hour:02d}:{now.minute:02d}"


def requested_date(query: str, now: datetime) -> str | None:
    """Finds the day the query asks about.

    Args:
        query: The user's question.
        now: The local time of the query.

    Returns:
        "YYYY-MM-DD" for a named weekday (the next one, counting today),
        today for "today"/"tonight", tomorrow for "tomorrow".
    """
    lowered = query.lower()

    # A named weekday, "sundays" included: the next one, counting today
    for word, weekday in WEEKDAYS.items():
        if re.search(rf"\b{word}s?\b", lowered):
            # Days until that weekday, counting today as zero
            ahead = (weekday - now.weekday()) % 7
            return (now.date() + timedelta(days=ahead)).isoformat()

    # Tomorrow's date
    if re.search(r"\btomorrow\b", lowered):
        return (now.date() + timedelta(days=1)).isoformat()

    # Today and tonight land on the same date
    if re.search(r"\b(today|tonight)\b", lowered):
        return now.date().isoformat()

    return None


def has_deadline(query: str) -> bool:
    """Tells whether the query asks to arrive by a clock time.

    Args:
        query: The user's question.

    Returns:
        True for deadline asks ("by 10am", "before 5:30 pm").
    """
    deadline = r"\b(by|before|at)\s*\d{1,2}(:\d{2})?\s*(am|pm)\b"
    return re.search(deadline, query.lower()) is not None


def departure_groups(rows: list[dict]) -> dict[tuple[str, int], list[str]]:
    """Groups catchable departures by route and direction.

    Args:
        rows: /predictions or /schedules records.

    Returns:
        (route_id, direction_id) -> ISO departure times, soonest first.
        Canceled and skipped trips are dropped, and so are arrival-only
        rows (trips that end at the stop).
    """
    groups = {}
    for row in rows:
        attributes = row["attributes"]
        # A canceled or skipped trip isn't a departure
        if attributes.get("schedule_relationship") in ("CANCELLED", "SKIPPED"):
            continue

        # No departure time means the trip ends at this stop
        if attributes["departure_time"] is None:
            continue

        # Pile times by route and direction
        key = (row["relationships"]["route"]["data"]["id"], attributes["direction_id"])
        groups.setdefault(key, []).append(attributes["departure_time"])

    # Sort
    for times in groups.values():
        times.sort(key=datetime.fromisoformat)
    return groups


def clock(iso_time: str) -> str:
    """Formats an ISO timestamp as a readable local time ("4:16 PM").

    Args:
        iso_time: An ISO 8601 timestamp.

    Returns:
        The clock time, no leading zero.
    """
    return datetime.fromisoformat(iso_time).strftime("%I:%M %p").lstrip("0")


def route_label(short_name: str, long_name: str, route_type: int) -> str:
    """Returns the spoken route name ("Route 77", "Red Line").

    Args:
        short_name: The route's short_name.
        long_name: The route's long_name.
        route_type: The GTFS route type code.

    Returns:
        "Route X" for buses; the branded long_name for everything else.
    """
    if route_type == 3:
        return f"Route {short_name}"
    return long_name


def render_next(
    route_id: str,
    direction_id: int,
    times: list[str],
    station_name: str,
    stop_id: str,
    live: bool,
    route_info: dict,
    retrieved_at: str,
) -> Row:
    """Builds one next-departures row shaped like a retrieved chunk.

    Args:
        route_id: The route these departures belong to.
        direction_id: 0 or 1, indexes the route's destinations.
        times: Upcoming ISO departure times, soonest first.
        station_name: The station's display name.
        stop_id: The station's MBTA id.
        live: Whether the times are live predictions.
        route_info: route_id -> (short_name, long_name, type, destinations).
        retrieved_at: When the fetch happened.

    Returns:
        A (id, kind, text, metadata, distance) row.
    """
    short_name, long_name, route_type, destinations = route_info[route_id]
    label = route_label(short_name, long_name, route_type)
    destination = destinations[direction_id]
    clocks = ", ".join(clock(time) for time in times)
    text = (
        f"{label} toward {destination} from {station_name}: next departures {clocks}."
    )

    # Label fallback times so the answer can't pass them off as live
    if not live:
        text += " Scheduled times, not live."
    metadata = {
        "route_id": route_id,
        "stop_id": stop_id,
        "direction_id": direction_id,
        "departure_times": times,
        "live": live,
        "retrieved_at": retrieved_at,
    }
    return (
        f"schedule:{route_id}:{stop_id}:{direction_id}",
        "schedule",
        text,
        metadata,
        0.0,
    )


def render_edge(
    kind: str,
    route_id: str,
    direction_id: int,
    time: str,
    station_name: str,
    stop_id: str,
    day_name: str,
    route_info: dict,
    retrieved_at: str,
) -> Row:
    """Builds one first-or-last departure row shaped like a retrieved chunk.

    Args:
        kind: "First" or "Last".
        route_id: The route the departure belongs to.
        direction_id: 0 or 1, indexes the route's destinations.
        time: The ISO departure time.
        station_name: The station's display name.
        stop_id: The station's MBTA id.
        day_name: The weekday asked about ("Saturday").
        route_info: route_id -> (short_name, long_name, type, destinations).
        retrieved_at: When the fetch happened.

    Returns:
        A (id, kind, text, metadata, distance) row.
    """
    short_name, long_name, route_type, destinations = route_info[route_id]
    label = route_label(short_name, long_name, route_type)
    text = (
        f"{kind} {label} toward {destinations[direction_id]} from {station_name} "
        f"on {day_name}: {clock(time)}."
    )
    metadata = {
        "route_id": route_id,
        "stop_id": stop_id,
        "direction_id": direction_id,
        "departure_times": [time],
        "live": False,
        "retrieved_at": retrieved_at,
    }
    row_id = f"schedule:{route_id}:{stop_id}:{direction_id}:{kind.lower()}"
    return (row_id, "schedule", text, metadata, 0.0)


def fetch_departures(query: str) -> list[Row]:
    """Fetches upcoming departures for the stops named in a query.

    Args:
        query: The user's question.

    Returns:
        Departure rows shaped like retrieved chunks. Live predictions
        first, scheduled times as the fallback; "first"/"last" questions
        read the schedule for the asked day.
    """
    # Local time for the service calculations
    now = datetime.now()
    retrieved_at = datetime.now(timezone.utc).isoformat()

    # Match the stations and routes the query names
    connection = connect()
    with connection.cursor() as cursor:
        station_ids = match_station_ids(cursor, query)
        route_ids = match_route_ids(cursor, query)
        if not station_ids:
            return []

        # Labels and destinations for the row text
        cursor.execute(ROUTE_INFO)
        route_info = {}
        for (
            route_id,
            short_name,
            long_name,
            route_type,
            destinations,
        ) in cursor.fetchall():
            route_info[route_id] = (
                short_name,
                long_name,
                int(route_type),
                destinations,
            )
        cursor.execute(STATION_NAMES, (station_ids,))
        station_names = dict(cursor.fetchall())

    # First and last questions read the schedule instead of predictions
    lowered = query.lower()
    wants_first = re.search(r"\bfirst\b", lowered) is not None
    wants_last = re.search(r"\blast\b", lowered) is not None

    rows = []
    for chunk_id in station_ids:
        stop_id = chunk_id.removeprefix("stop:")
        station_name = station_names[chunk_id]

        # Get 150 rows
        params = {"filter[stop]": stop_id, "sort": "departure_time", "page[limit]": 150}
        if route_ids:
            params["filter[route]"] = ",".join(route_ids)

        # First and last run on the schedule for the asked day
        if wants_first or wants_last:
            target = requested_date(query, now) or now.date().isoformat()
            day_name = date.fromisoformat(target).strftime("%A")
            # Last reads the day backward from 3 PM
            edges = []
            if wants_first:
                edges.append(("First", {}, 0))
            if wants_last:
                last_extra = {"sort": "-departure_time", "filter[min_time]": "15:00"}
                edges.append(("Last", last_extra, -1))
            for kind, extra, pick in edges:
                records = fetch("/schedules", {**params, **extra, "date": target})
                for (route_id, direction_id), times in departure_groups(
                    records
                ).items():
                    # Diversion shuttles aren't in the routes table
                    if route_id not in route_info:
                        continue
                    rows.append(
                        render_edge(
                            kind,
                            route_id,
                            direction_id,
                            times[pick],
                            station_name,
                            stop_id,
                            day_name,
                            route_info,
                            retrieved_at,
                        )
                    )
            continue

        # Next departures: live predictions, today's schedule as the fallback
        live = True
        groups = departure_groups(fetch("/predictions", params))
        if not groups:
            live = False
            target, minimum = service_day(now)
            records = fetch(
                "/schedules", {**params, "date": target, "filter[min_time]": minimum}
            )
            groups = departure_groups(records)
        for (route_id, direction_id), times in groups.items():
            # Diversion shuttles aren't in the routes table
            if route_id not in route_info:
                continue
            rows.append(
                render_next(
                    route_id,
                    direction_id,
                    times[:NEXT_DEPARTURES],
                    station_name,
                    stop_id,
                    live,
                    route_info,
                    retrieved_at,
                )
            )

    # Nothing running and nothing scheduled
    if not rows:
        text = f"No departures found for this stop as of {clock(now.isoformat())}."
        return [
            ("schedule:none", "schedule", text, {"retrieved_at": retrieved_at}, 0.0)
        ]
    return rows


if __name__ == "__main__":
    query = sys.argv[1]
    for chunk_id, kind, text, metadata, distance in fetch_departures(query):
        print(f"{chunk_id} {text}")
