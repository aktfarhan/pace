"""Plan A-to-B transit trips by scanning the day's GTFS timetable."""

import sys
from datetime import date, datetime, time, timedelta, timezone

from backend.classify import ParsedQuery
from backend.retrieve import Row, match_station_ids
from backend.schedules import SERVICE_ROLLOVER_HOUR, clock, requested_date, route_label
from backend.timetable import (
    active_service_ids,
    load_connections,
    load_footpaths,
    load_routes,
    load_stops,
    load_trips,
)
from data.schema import connect

INFINITY = float("inf")


def service_moment(service_date: date, seconds: int) -> datetime:
    """Turns seconds into a service day back into datetime.

    Args:
        service_date: The service day's date.
        seconds: Seconds after that day's midnight.

    Returns:
        The full datetime.
    """
    return datetime.combine(service_date, time()) + timedelta(seconds=seconds)


def service_clock(service_date: date, seconds: int) -> str:
    """Formats seconds into a service day as a readable clock time.

    Args:
        service_date: The service day's date.
        seconds: Seconds since the day's midnight.

    Returns:
        The clock time ("10:17 PM").
    """
    return clock(service_moment(service_date, seconds).isoformat())


def station_name(stop_id: str, names: dict, parents: dict) -> str:
    """Returns the station-level name for a stop.

    Args:
        stop_id: A stop or platform id.
        names: stop_id -> name.
        parents: platform id -> parent station id.

    Returns:
        The parent station's name when it's available.
    """
    return names[parents.get(stop_id, stop_id)]


def scan(
    connections: list[tuple], footpaths: dict, sources: dict, targets: set
) -> tuple:
    """Finds the earliest way to reach a target stop.

    Args:
        connections: The day's connections, sorted by departure.
        footpaths: The walking transfers at each stop.
        sources: The starting platforms, each with the trip's start time.
        targets: The stops that count as reaching the destination.

    Returns:
        Tuple of (best_stop, earliest, arrived_via, boarded):
        - best_stop: the reached target stop
        - earliest: stop_id -> best arrival seconds
        - arrived_via: stop_id -> the ride or walk that got there
        - boarded: trip_id -> the connection where it was caught
    """
    earliest = dict(sources)
    arrived_via = {}
    boarded = {}

    # Walks available from the starting stops
    for stop, ready_seconds in sources.items():
        for to_stop, walk_seconds in footpaths.get(stop, []):
            arrival = ready_seconds + walk_seconds
            if arrival < earliest.get(to_stop, INFINITY):
                earliest[to_stop] = arrival
                arrived_via[to_stop] = ("walk", stop, walk_seconds)

    best_arrival = INFINITY
    best_stop = None

    for connection in connections:
        (
            departure_seconds,
            departure_stop,
            arrival_seconds,
            arrival_stop,
            trip_id,
            boardable,
            alightable,
        ) = connection

        # Stop when departures pass the best arrival
        if departure_seconds >= best_arrival:
            break

        # Board a trip only when its stop is reached by departure
        if trip_id not in boarded:
            ready = earliest.get(departure_stop, INFINITY)
            if not boardable or ready > departure_seconds:
                continue
            boarded[trip_id] = connection

        # An earlier arrival at this stop
        if alightable and arrival_seconds < earliest.get(arrival_stop, INFINITY):
            earliest[arrival_stop] = arrival_seconds
            arrived_via[arrival_stop] = ("ride", connection)

            # Update the best
            if arrival_stop in targets and arrival_seconds < best_arrival:
                best_arrival = arrival_seconds
                best_stop = arrival_stop

            # Walks from the new arrival
            for to_stop, walk_seconds in footpaths.get(arrival_stop, []):
                walk_arrival = arrival_seconds + walk_seconds
                if walk_arrival < earliest.get(to_stop, INFINITY):
                    earliest[to_stop] = walk_arrival
                    arrived_via[to_stop] = ("walk", arrival_stop, walk_seconds)

                    # Update the best
                    if to_stop in targets and walk_arrival < best_arrival:
                        best_arrival = walk_arrival
                        best_stop = to_stop

    return best_stop, earliest, arrived_via, boarded


def build_legs(
    best_stop: str, earliest: dict, arrived_via: dict, boarded: dict
) -> list[dict]:
    """Turns the scan's result into journey legs.

    Args:
        best_stop: The reached target stop.
        earliest: Best arrival seconds per stop.
        arrived_via: The ride or walk that got to each stop.
        boarded: The connection where each trip was caught.

    Returns:
        Legs in travel order. Rides have trip_id, board_stop, and
        alight_stop; walks carry from_stop and to_stop. Every leg
        has depart_seconds and arrive_seconds.
    """
    legs = []
    stop = best_stop

    # Trace the path backward from the destination
    while stop in arrived_via:
        step = arrived_via[stop]

        # A walk leg
        if step[0] == "walk":
            _, from_stop, walk_seconds = step
            legs.append(
                {
                    "kind": "walk",
                    "from_stop": from_stop,
                    "to_stop": stop,
                    "depart_seconds": earliest[stop] - walk_seconds,
                    "arrive_seconds": earliest[stop],
                }
            )
            stop = from_stop

        # A ride leg
        else:
            connection = step[1]
            trip_id = connection[4]
            boarding = boarded[trip_id]
            legs.append(
                {
                    "kind": "ride",
                    "trip_id": trip_id,
                    "board_stop": boarding[1],
                    "alight_stop": connection[3],
                    "depart_seconds": boarding[0],
                    "arrive_seconds": connection[2],
                }
            )
            stop = boarding[1]

    # Flip into travel order
    legs.reverse()
    return legs


def render_legs(
    legs: list[dict],
    service_date: date,
    names: dict,
    parents: dict,
    routes: dict,
    trips: dict,
    retrieved_at: str,
) -> list[Row]:
    """Turns journey legs into citable plan rows.

    Args:
        legs: The journey's legs in travel order.
        service_date: The service day planned on.
        names: The display name for every stop.
        parents: Platform-to-station links.
        routes: The label fields for every route.
        trips: The route and headsign for every trip.
        retrieved_at: When the plan was computed.

    Returns:
        Rows shaped like retrieved chunks.
    """
    first, last = legs[0], legs[-1]
    start_stop = first["board_stop"] if first["kind"] == "ride" else first["from_stop"]
    end_stop = last["alight_stop"] if last["kind"] == "ride" else last["to_stop"]

    # Rides minus one is the transfer count
    rides = 0
    for leg in legs:
        if leg["kind"] == "ride":
            rides += 1
    transfers = max(rides - 1, 0)

    # The summary row
    minutes = (last["arrive_seconds"] - first["depart_seconds"] + 59) // 60
    text = (
        f"{station_name(start_stop, names, parents)} to "
        f"{station_name(end_stop, names, parents)}: leave "
        f"{service_clock(service_date, first['depart_seconds'])}, arrive "
        f"{service_clock(service_date, last['arrive_seconds'])}, {minutes} min."
    )

    # Transfer info
    if transfers == 1:
        text += " One transfer."
    elif transfers > 1:
        text += f" {transfers} transfers."

    text += " Scheduled times, not live."
    metadata = {
        "origin_stop": start_stop,
        "destination_stop": end_stop,
        "depart": service_moment(service_date, first["depart_seconds"]).isoformat(),
        "arrive": service_moment(service_date, last["arrive_seconds"]).isoformat(),
        "transfers": transfers,
        "service_date": service_date.isoformat(),
        "live": False,
        "retrieved_at": retrieved_at,
    }
    rows = [("plan:summary", "plan", text, metadata, 0.0)]

    # One row per leg
    for index, leg in enumerate(legs):
        depart = service_moment(service_date, leg["depart_seconds"]).isoformat()
        arrive = service_moment(service_date, leg["arrive_seconds"]).isoformat()
        if leg["kind"] == "walk":
            minutes = (leg["arrive_seconds"] - leg["depart_seconds"] + 59) // 60
            from_name = station_name(leg["from_stop"], names, parents)
            to_name = station_name(leg["to_stop"], names, parents)

            # A walk inside a station is a platform transfer
            if from_name == to_name:
                text = f"Transfer at {to_name}"
            else:
                text = f"Walk from {from_name} to {to_name}"
            if minutes:
                text += f", {minutes} min"
            text += "."
            metadata = {
                "from_stop": leg["from_stop"],
                "to_stop": leg["to_stop"],
                "depart": depart,
                "arrive": arrive,
                "retrieved_at": retrieved_at,
            }
        else:
            route_id, headsign = trips[leg["trip_id"]]
            short_name, long_name, route_type = routes[route_id]
            label = route_label(short_name, long_name, route_type)
            text = (
                f"{label} toward {headsign} from "
                f"{station_name(leg['board_stop'], names, parents)}: board "
                f"{service_clock(service_date, leg['depart_seconds'])}, off at "
                f"{station_name(leg['alight_stop'], names, parents)} "
                f"{service_clock(service_date, leg['arrive_seconds'])}."
            )
            metadata = {
                "route_id": route_id,
                "trip_id": leg["trip_id"],
                "board_stop": leg["board_stop"],
                "alight_stop": leg["alight_stop"],
                "depart": depart,
                "arrive": arrive,
                "live": False,
                "retrieved_at": retrieved_at,
            }
        rows.append((f"plan:{index}", "plan", text, metadata, 0.0))

    return rows


def plan_trip(query: str, parsed: ParsedQuery) -> list[Row]:
    """Plans the trip a query asks for from the GTFS timetable.

    Args:
        query: The user's question.
        parsed: The classifier's read of the query.

    Returns:
        Plan rows shaped like retrieved chunks: a summary, then one row
        per leg. Empty when either endpoint is missing or unknown; a
        no-route row when the scan finds nothing.
    """
    now = datetime.now()
    retrieved_at = datetime.now(timezone.utc).isoformat()

    # Both endpoints must resolve to stations
    origin, destination = parsed["origin"], parsed["destination"]
    if not origin or not destination:
        return []

    # Match station ids
    connection = connect()
    with connection.cursor() as cursor:
        origin_ids = match_station_ids(cursor, origin)
        destination_ids = match_station_ids(cursor, destination)
    if not origin_ids or not destination_ids:
        return []

    # Strip chunk ids to station ids
    origin_parents = [chunk_id.removeprefix("stop:") for chunk_id in origin_ids]
    destination_parents = [
        chunk_id.removeprefix("stop:") for chunk_id in destination_ids
    ]

    # The same station on both ends
    if set(origin_parents) & set(destination_parents):
        text = "Origin and destination are the same stop."
        return [("plan:none", "plan", text, {"retrieved_at": retrieved_at}, 0.0)]

    # The service day and the departure seconds on it
    if parsed["day"]:
        # A named day plans that date around the current time
        service_date = date.fromisoformat(requested_date(parsed["day"], now))
        depart_seconds = now.hour * 3600 + now.minute * 60
    elif now.hour < SERVICE_ROLLOVER_HOUR:
        # Past midnight the service clock keeps counting
        service_date = now.date() - timedelta(days=1)
        depart_seconds = (now.hour + 24) * 3600 + now.minute * 60
    else:
        service_date = now.date()
        depart_seconds = now.hour * 3600 + now.minute * 60

    # The day's timetable
    routes = load_routes()
    footpaths = load_footpaths()
    services = active_service_ids(service_date)
    trips = load_trips(services)
    connections = load_connections(trips)
    names, children, parents = load_stops()

    # Sources and targets from the stations' platforms
    sources = {}
    for parent in origin_parents:
        for child in children.get(parent, [parent]):
            sources[child] = depart_seconds

    # Arrival at any destination platform counts
    targets = set()
    for parent in destination_parents:
        targets.update(children.get(parent, [parent]))

    # Find the earliest arrival
    best_stop, earliest, arrived_via, boarded = scan(
        connections, footpaths, sources, targets
    )

    # Nothing reachable on the day's timetable
    if best_stop is None:
        text = (
            f"No route found from {names[origin_parents[0]]} to "
            f"{names[destination_parents[0]]} as of "
            f"{service_clock(service_date, depart_seconds)}."
        )
        return [("plan:none", "plan", text, {"retrieved_at": retrieved_at}, 0.0)]

    legs = build_legs(best_stop, earliest, arrived_via, boarded)
    return render_legs(legs, service_date, names, parents, routes, trips, retrieved_at)


if __name__ == "__main__":
    from backend.classify import classify

    query = sys.argv[1]
    parsed = classify(query)
    for chunk_id, kind, text, metadata, distance in plan_trip(query, parsed):
        print(f"{chunk_id} {text}")
