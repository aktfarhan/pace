"""Fetch live departure predictions and scheduled times for the stops named in a query."""

import sys
from datetime import date, datetime, timedelta, timezone

import numpy as np

from backend.assistant.parse import ParsedQuery
from backend.core.clock import in_boston, moment_at, now_in_boston, parse_clock
from backend.mbta.client import fetch
from backend.mbta.stations import Station, find_stations
from backend.assistant.retrieve import Row, match_route_ids
from backend.planner.days import load_service_day
from backend.planner.timetable import (
    SERVICE_ROLLOVER_HOUR,
    gtfs_stamp,
    last_service_date,
    load_stops,
    service_date_at,
    service_seconds,
)
from backend.core.db import borrow

# Upcoming departures shown per route and direction
NEXT_DEPARTURES = 3

# The row id used when the stop has nothing scheduled
NO_DEPARTURES = "schedule:none"

# The row id used for a date past the timetable
PAST_TIMETABLE = "schedule:beyond"

# The daytime window "how often" answers describe
DAYTIME_START = 7 * 3600
DAYTIME_END = 19 * 3600

# Fewest departures that make a "how often" group
HEADWAY_MIN_TRIPS = 4

# A start point needs this share of the route's busiest one
HEADWAY_SHARE = 0.25

# Most "how often" groups in one answer
HEADWAY_GROUPS = 4

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

# route_id -> (short_name, long_name, type, color, destinations)
RouteInfo = dict[str, tuple[str, str, int, str, list[str]]]


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
        day: The parsed day ("saturday", "today", "tonight", "tomorrow",
            or a date "2026-11-16"), or None when the query named no day.
        now: The time of the query.

    Returns:
        "YYYY-MM-DD" for a named weekday (the next one, counting today),
        today for "today"/"tonight", tomorrow for "tomorrow", and a
        date as it is.
    """
    if day is None:
        return None

    # A date the rules read
    if day[:1].isdigit():
        try:
            return date.fromisoformat(day).isoformat()
        except ValueError:
            return None

    today = service_date_at(now)

    # Tomorrow's date
    if day == "tomorrow":
        return (today + timedelta(days=1)).isoformat()

    # Today and tonight land on the same date
    if day in ("today", "tonight"):
        return today.isoformat()

    # A named weekday: the next one, counting today as zero days ahead
    if day in WEEKDAYS:
        ahead = (WEEKDAYS[day] - today.weekday()) % 7
        return (today + timedelta(days=ahead)).isoformat()

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
    """Formats an ISO timestamp as a readable Boston time ("4:16 PM").

    Args:
        iso_time: An ISO 8601 timestamp.

    Returns:
        The clock time, no leading zero.
    """
    moment = in_boston(datetime.fromisoformat(iso_time))
    return moment.strftime("%I:%M %p").lstrip("0")


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
    day_name: str | None = None,
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
        day_name: The day read ("Saturday, November 1"), when not today.

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

    # Say which day the times are for
    if day_name:
        text = f"On {day_name}: {text}"
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
        "day": day_name,
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


def spoken_day(asked: date) -> str:
    """Writes a date the way an answer says it.

    Args:
        asked: The date.

    Returns:
        "Saturday, November 1".
    """
    return asked.strftime("%A, %B %d").replace(" 0", " ")


def read_route_info() -> RouteInfo:
    """Reads the route names, colors and destinations.

    Returns:
        Route info by route id.
    """
    route_info: RouteInfo = {}
    with borrow() as connection, connection.cursor() as cursor:
        cursor.execute(ROUTE_INFO)
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
    return route_info


def spacing(times: list[int]) -> tuple[int, int, bool] | None:
    """Measures the usual gap between departures.

    Args:
        times: Departure times in seconds into the service day.

    Returns:
        Tuple of (low, high, daytime): the middle half of the gaps in
        minutes, and whether they come from 7 AM to 7 PM.
    """
    times = sorted(set(times))
    pairs = list(zip(times, times[1:]))
    if not pairs:
        return None

    # Daytime gaps when there are enough of them
    daytime = [(b - a) / 60 for a, b in pairs if a >= DAYTIME_START and b <= DAYTIME_END]
    gaps = daytime if len(daytime) >= 3 else [(b - a) / 60 for a, b in pairs]
    gaps.sort()
    low = round(gaps[len(gaps) // 4])
    high = round(gaps[(3 * len(gaps)) // 4])
    return max(low, 1), max(high, 1), gaps is daytime


def headway_groups(
    stations: list[Station], route_ids: list[str], asked: date
) -> dict[tuple[str, str, str, str], list[int]]:
    """Collects departures from the timetable for a "how often" answer.

    Args:
        stations: The stops asked about, or empty for the whole route.
        route_ids: The routes asked about, or empty for every route.
        asked: The service date.

    Returns:
        (route_id, stop name, stop id, headsign) -> departure seconds.
    """
    stamp = gtfs_stamp()
    day = load_service_day(asked, stamp)
    names, children, parents, _ = load_stops(stamp)
    wanted = set(route_ids)

    # Each trip's route and headsign, by trip number
    trip_routes = []
    trip_signs = []
    for trip_id in day.trip_ids:
        route_id, headsign = day.trips[trip_id]
        trip_routes.append(route_id)
        trip_signs.append(headsign)

    groups: dict[tuple[str, str, str, str], list[int]] = {}

    # Departures from the stop's platforms
    if stations:
        position = {stop: index for index, stop in enumerate(day.stops)}
        for station in stations:
            platforms = []
            for platform in children.get(station["id"], [station["id"]]):
                if platform in position:
                    platforms.append(position[platform])
            boards = np.isin(day.from_stops, platforms) & day.boardable.astype(bool)
            for at in np.flatnonzero(boards).tolist():
                trip = int(day.trip_of[at])
                if wanted and trip_routes[trip] not in wanted:
                    continue
                key = (trip_routes[trip], station["name"], station["id"], trip_signs[trip])
                groups.setdefault(key, []).append(int(day.departures[at]))
        return groups

    # Where each trip of the route starts
    signs: dict[tuple[str, str, str], list[str]] = {}
    for trip, route_id in enumerate(trip_routes):
        if route_id not in wanted:
            continue
        begins, ends = day.trip_starts[trip], day.trip_starts[trip + 1]
        if begins == ends:
            continue
        at = int(day.trip_order[begins])
        stop = day.stops[int(day.from_stops[at])]
        parent = parents.get(stop, stop)
        start = (route_id, names.get(parent, stop), parent)
        groups.setdefault((*start, ""), []).append(int(day.departures[at]))
        signs.setdefault(start, []).append(trip_signs[trip])

    # Each start is labeled by where most of its trips go
    labeled = {}
    for (route_id, name, stop_id, _), times in groups.items():
        headsigns = signs[(route_id, name, stop_id)]
        headsign = max(set(headsigns), key=headsigns.count)
        labeled[(route_id, name, stop_id, headsign)] = times
    return labeled


def headway_rows(
    stations: list[Station],
    route_ids: list[str],
    asked: date,
    route_info: RouteInfo,
    retrieved_at: str,
) -> list[Row]:
    """Answers how often a route runs from the asked day's timetable.

    Args:
        stations: The stops asked about, or empty for the whole route.
        route_ids: The routes asked about.
        asked: The service date.
        route_info: Route names, color, and destinations by route id.
        retrieved_at: When the read happened.

    Returns:
        One row per route, stop and direction, busiest first.
    """
    groups = headway_groups(stations, route_ids, asked)
    day_name = spoken_day(asked)

    # Each route's busiest group sets the bar for the rest
    busiest: dict[str, int] = {}
    for (route_id, _, _, _), times in groups.items():
        busiest[route_id] = max(busiest.get(route_id, 0), len(times))

    kept = []
    for key, times in groups.items():
        route_id = key[0]
        if route_id not in route_info or len(times) < HEADWAY_MIN_TRIPS:
            continue
        if len(times) < HEADWAY_SHARE * busiest[route_id]:
            continue
        kept.append((key, times))
    kept.sort(key=lambda item: len(item[1]), reverse=True)

    rows = []
    for (route_id, station_name, stop_id, headsign), times in kept[:HEADWAY_GROUPS]:
        measured = spacing(times)
        if measured is None:
            continue
        low, high, daytime = measured
        short_name, long_name, route_type, _, _ = route_info[route_id]
        label = route_label(short_name, long_name, route_type)
        first = clock(moment_at(asked, min(times)).isoformat())
        last = clock(moment_at(asked, max(times)).isoformat())

        every = f"{low} min" if low == high else f"{low} to {high} min"
        window = " from 7 AM to 7 PM" if daytime else ""
        text = (
            f"{label} from {station_name} toward {headsign} on {day_name}: "
            f"about every {every}{window}, {len(times)} departures "
            f"from {first} to {last}. Scheduled times, not live."
        )
        metadata = {
            "route_id": route_id,
            "stop_id": stop_id,
            "label": label,
            "station": station_name,
            "destination": headsign,
            "day": day_name,
            "headway_minutes": [low, high],
            "trips": len(times),
            "edge": None,
            "live": False,
            "retrieved_at": retrieved_at,
        }
        slug = headsign.lower().replace(" ", "-").replace("/", "-")
        row_id = f"schedule:{route_id}:{stop_id}:headway:{slug}"
        rows.append((row_id, "schedule", text, metadata, 0.0))
    return rows


def fetch_departures(parsed: ParsedQuery) -> list[Row]:
    """Fetches departures for the stop the user leaves from.

    Args:
        parsed: The read of the query.

    Returns:
        Departure rows shaped like retrieved chunks.
    """
    # Boston time for the service calculations
    now = now_in_boston()
    retrieved_at = datetime.now(timezone.utc).isoformat()

    # The day asked about, today when none is named
    today = service_date_at(now)
    target = requested_date(parsed["day"], now)
    asked_date = date.fromisoformat(target) if target else today
    day_name = spoken_day(asked_date)

    # The boarding stop and the route come from parse
    stations = find_stations(parsed["origin"])
    route = parsed["route"]
    route_ids = match_route_ids(route) if route else []
    headway = parsed.get("headway", False)
    if not stations and not (headway and route_ids):
        return []

    # A date past the end of the downloaded timetable
    end = last_service_date(gtfs_stamp())
    if end is not None and asked_date > end:
        text = (
            f"The timetable only goes through {spoken_day(end)}, "
            f"so there are no times for {day_name} yet."
        )
        return [(PAST_TIMETABLE, "schedule", text, {"retrieved_at": retrieved_at}, 0.0)]

    # Labels and destinations for the row text
    route_info = read_route_info()

    # How often reads the gaps in that day's timetable
    if headway:
        rows = headway_rows(stations, route_ids, asked_date, route_info, retrieved_at)
        if rows:
            return rows
        text = f"Nothing scheduled for this route on {day_name}."
        return [(NO_DEPARTURES, "schedule", text, {"retrieved_at": retrieved_at}, 0.0)]

    # First and last questions read the schedule instead of predictions
    wants_first = parsed["edge"] in ("first", "both")
    wants_last = parsed["edge"] in ("last", "both")
    target = asked_date.isoformat()

    # Next departures on another day or from a named time read the schedule
    leave = parse_clock(parsed.get("leave_at"))
    live = asked_date == today and leave is None
    other_day = day_name if asked_date != today else None

    # The schedule's start: the named time, else now's clock on that day
    if leave is None:
        leave = now.hour * 3600 + now.minute * 60
    if leave < SERVICE_ROLLOVER_HOUR * 3600:
        leave += 24 * 3600
    minimum = f"{leave // 3600:02d}:{leave % 3600 // 60:02d}"

    rows = []
    for station in stations:
        stop_id = station["id"]
        station_name = station["name"]

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
                            asked_date.strftime("%A"),
                            route_info,
                            retrieved_at,
                        )
                    )
            continue

        # Next departures: live predictions, today's schedule as the fallback
        groups = {}
        if live:
            groups = departure_groups(fetch("/predictions", params)["data"])
        if not groups:
            if live:
                target, minimum = service_day(now)
            records = fetch(
                "/schedules", {**params, "date": target, "filter[min_time]": minimum}
            )["data"]
            groups = departure_groups(records)
            found_live = False
        else:
            found_live = True
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
                    found_live,
                    route_info,
                    retrieved_at,
                    other_day,
                )
            )

    # Nothing running and nothing scheduled
    if not rows:
        if wants_first or wants_last or other_day:
            spoken_date = asked_date.strftime("%B %d, %Y").replace(" 0", " ")
            text = f"No departures found for this stop on {spoken_date}."
        else:
            text = f"No departures found for this stop as of {clock(now.isoformat())}."
        return [(NO_DEPARTURES, "schedule", text, {"retrieved_at": retrieved_at}, 0.0)]
    return rows


if __name__ == "__main__":
    from backend.assistant.parse import read_question

    query = sys.argv[1]
    parsed = read_question(query)
    for chunk_id, kind, text, metadata, distance in fetch_departures(parsed):
        print(f"{chunk_id} {text}")
