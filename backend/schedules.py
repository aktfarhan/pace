"""Fetch live departure predictions and scheduled times for the stops named in a query."""

import sys
from datetime import date, datetime, timedelta, timezone

from backend.classify import ParsedQuery
from backend.mbta import fetch
from backend.retrieve import Row, match_route_ids, match_station_ids
from backend.timetable import service_date_at, service_seconds
from data.schema import connect

# Upcoming departures shown per route and direction
NEXT_DEPARTURES = 3

# The row id used when the stop has nothing scheduled
NO_DEPARTURES = "schedule:none"


def live_departures(route_id: str, board_stop: str, alight_stop: str) -> list[str]:
    """Fetches the next live departures that reach the user's stop.

    Args:
        route_id: The route the rider boards.
        board_stop: The boarding platform's id.
        alight_stop: The alighting platform's id.

    Returns:
        Up to three ISO departure times, soonest first.
    """
    params = {
        "filter[route]": route_id,
        "filter[stop]": f"{board_stop},{alight_stop}",
        "sort": "departure_time",
        "page[limit]": 30,
    }

    # A train that works shows up at both stops
    boards = {}
    reaches = {}
    for record in fetch("/predictions", params)["data"]:
        stop = record["relationships"]["stop"]["data"]["id"]
        trip = record["relationships"]["trip"]["data"]["id"]
        attributes = record["attributes"]

        # When this train leaves the boarding stop
        if stop == board_stop and attributes["departure_time"] is not None:
            boards[trip] = attributes["departure_time"]

        # When this train reaches the rider's stop
        if stop == alight_stop:
            arrival = attributes["arrival_time"] or attributes["departure_time"]
            if arrival is not None:
                reaches[trip] = arrival

    # Soonest boarding first
    times = []
    for trip, departure in sorted(boards.items(), key=lambda pair: pair[1]):
        # Keep trains that board first and reach the rider's stop after
        if trip in reaches and departure < reaches[trip]:
            times.append(departure)

        if len(times) == NEXT_DEPARTURES:
            break

    return times


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
           metadata->>'color' AS color,
           metadata->'direction_destinations' AS direction_destinations
    FROM chunks WHERE kind = 'route';
"""
STATION_NAMES = """
    SELECT id, metadata->>'name' AS name
    FROM chunks WHERE id = ANY(%s);
"""

# route_id -> (short_name, long_name, type, color, destinations)
RouteInfo = dict[str, tuple[str, str, int, str, list[str]]]


def service_day(now: datetime) -> tuple[str, str]:
    """Returns the MBTA service date and clock time for a local moment.

    Args:
        now: The local time of the query.

    Returns:
        Tuple of (date "YYYY-MM-DD", time "HH:MM"). Before 3 AM the
        service day is still yesterday and hours count past 24, so a
        12:40 AM query asks for yesterday's date at 24:40.
    """
    hour = service_seconds(now) // 3600
    return service_date_at(now).isoformat(), f"{hour:02d}:{now.minute:02d}"


def requested_date(day: str | None, now: datetime) -> str | None:
    """Turns the parsed query's day into a date.

    Args:
        day: The parsed day ("saturday", "today", "tonight", "tomorrow"),
            or None when the query named no day.
        now: The local time of the query.

    Returns:
        "YYYY-MM-DD" for a named weekday (the next one, counting today),
        today for "today"/"tonight", tomorrow for "tomorrow".
    """
    if day is None:
        return None

    # Tomorrow's date
    if day == "tomorrow":
        return (now.date() + timedelta(days=1)).isoformat()

    # Today and tonight land on the same date
    if day in ("today", "tonight"):
        return now.date().isoformat()

    # A named weekday: the next one, counting today as zero days ahead
    if day in WEEKDAYS:
        ahead = (WEEKDAYS[day] - now.weekday()) % 7
        return (now.date() + timedelta(days=ahead)).isoformat()

    return None


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
    route_info: RouteInfo,
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
        route_info: Route names, color, and destinations by route id.
        retrieved_at: When the fetch happened.

    Returns:
        A (id, kind, text, metadata, distance) row.
    """
    short_name, long_name, route_type, color, destinations = route_info[route_id]
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
        "short_name": short_name,
        "label": label,
        "route_type": route_type,
        "color": color,
        "station": station_name,
        "destination": destination,
        "departure_times": times,
        "edge": None,
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


def edge_groups(
    records: list[dict], headsigns: dict[str, str]
) -> dict[tuple[str, int, str], list[str]]:
    """Groups catchable departures by route and headsign.

    Args:
        records: /schedules records.
        headsigns: trip id -> the trip's headsign.

    Returns:
        (route_id, direction_id, headsign) -> ISO departure times.
    """
    groups = {}
    for record in records:
        attributes = record["attributes"]

        # No departure time means the trip ends at this stop
        if attributes["departure_time"] is None:
            continue

        # No headsign means the payload didn't include the trip
        trip = record["relationships"]["trip"]["data"]["id"]
        headsign = headsigns.get(trip)
        if headsign is None:
            continue

        # Pile times by route, direction, and headsign
        key = (
            record["relationships"]["route"]["data"]["id"],
            attributes["direction_id"],
            headsign,
        )
        groups.setdefault(key, []).append(attributes["departure_time"])

    # Sort
    for times in groups.values():
        times.sort(key=datetime.fromisoformat)

    return groups


def render_edge(
    kind: str,
    route_id: str,
    direction_id: int,
    headsign: str,
    time: str,
    station_name: str,
    stop_id: str,
    day_name: str,
    route_info: RouteInfo,
    retrieved_at: str,
) -> Row:
    """Builds one first-or-last departure row shaped like a retrieved chunk.

    Args:
        kind: "First" or "Last".
        route_id: The route the departure belongs to.
        direction_id: 0 or 1, the direction the trip runs.
        headsign: The destination the train shows.
        time: The ISO departure time.
        station_name: The station's display name.
        stop_id: The station's MBTA id.
        day_name: The weekday asked about ("Saturday").
        route_info: Route names, color, and destinations by route id.
        retrieved_at: When the fetch happened.

    Returns:
        A (id, kind, text, metadata, distance) row.
    """
    short_name, long_name, route_type, _, _ = route_info[route_id]
    label = route_label(short_name, long_name, route_type)
    edge = kind.lower()
    text = (
        f"{kind} {label} toward {headsign} from {station_name} "
        f"on {day_name}: {clock(time)}."
    )
    metadata = {
        "route_id": route_id,
        "stop_id": stop_id,
        "direction_id": direction_id,
        "label": label,
        "station": station_name,
        "destination": headsign,
        "day": day_name,
        "departure_times": [time],
        "edge": edge,
        "live": False,
        "retrieved_at": retrieved_at,
    }
    slug = headsign.lower().replace(" ", "-").replace("/", "-")
    row_id = f"schedule:{route_id}:{stop_id}:{direction_id}:{edge}:{slug}"
    return (row_id, "schedule", text, metadata, 0.0)


def fetch_departures(parsed: ParsedQuery) -> list[Row]:
    """Fetches upcoming departures for the stop the user leaves from.

    Args:
        parsed: The classifier's read of the query.

    Returns:
        Departure rows shaped like retrieved chunks. Live predictions
        first, scheduled times as the fallback; "first"/"last" questions
        read the schedule for the asked day.
    """
    # Local time for the service calculations
    now = datetime.now()
    retrieved_at = datetime.now(timezone.utc).isoformat()

    # The boarding stop and the route come from parse
    connection = connect()
    with connection.cursor() as cursor:
        origin = parsed["origin"]
        station_ids = match_station_ids(cursor, origin) if origin else []

        route = parsed["route"]
        route_ids = match_route_ids(cursor, route) if route else []
        if not station_ids:
            return []

        # Labels and destinations for the row text
        cursor.execute(ROUTE_INFO)
        route_info: RouteInfo = {}
        for (
            route_id,
            short_name,
            long_name,
            route_type,
            color,
            destinations,
        ) in cursor.fetchall():
            route_info[route_id] = (
                short_name,
                long_name,
                int(route_type),
                color,
                destinations,
            )
        cursor.execute(STATION_NAMES, (station_ids,))
        station_names = dict(cursor.fetchall())

    # First and last questions read the schedule instead of predictions
    wants_first = parsed["edge"] in ("first", "both")
    wants_last = parsed["edge"] in ("last", "both")

    # The service date those questions read
    spoken_date = ""
    if wants_first or wants_last:
        target = requested_date(parsed["day"], now) or now.date().isoformat()
        asked = date.fromisoformat(target)
        day_name = asked.strftime("%A")

        # The date alone
        spoken_date = asked.strftime("%B %d, %Y").replace(" 0", " ")

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
            # Last reads the day backward from 3 PM
            edges = []
            if wants_first:
                edges.append(("First", {}, 0))
            if wants_last:
                last_extra = {"sort": "-departure_time", "filter[min_time]": "15:00"}
                edges.append(("Last", last_extra, -1))
            for kind, extra, pick in edges:
                asked = {**params, **extra, "date": target, "include": "trip"}
                payload = fetch("/schedules", asked)

                # The headsign each trip shows
                headsigns = {}
                for included in payload.get("included", []):
                    if included["type"] == "trip":
                        headsigns[included["id"]] = included["attributes"]["headsign"]

                groups = edge_groups(payload["data"], headsigns)
                for (route_id, direction_id, headsign), times in groups.items():
                    # Diversion shuttles aren't in the routes table
                    if route_id not in route_info:
                        continue
                    rows.append(
                        render_edge(
                            kind,
                            route_id,
                            direction_id,
                            headsign,
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
        groups = departure_groups(fetch("/predictions", params)["data"])
        if not groups:
            live = False
            target, minimum = service_day(now)
            records = fetch(
                "/schedules", {**params, "date": target, "filter[min_time]": minimum}
            )["data"]
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
        if spoken_date:
            text = f"No departures found for this stop on {spoken_date}."
        else:
            text = f"No departures found for this stop as of {clock(now.isoformat())}."
        return [(NO_DEPARTURES, "schedule", text, {"retrieved_at": retrieved_at}, 0.0)]
    return rows


if __name__ == "__main__":
    from backend.classify import classify

    query = sys.argv[1]
    parsed = classify(query)
    for chunk_id, kind, text, metadata, distance in fetch_departures(parsed):
        print(f"{chunk_id} {text}")
