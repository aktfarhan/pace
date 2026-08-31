"""Plan A-to-B transit trips by scanning the day's GTFS timetable."""

import sys
from datetime import date, datetime, timedelta, timezone

from backend.classify import ParsedQuery
from backend.planner.ends import resolve_endpoint, trip_times, walk_between
from backend.planner.legs import (
    build_legs,
    mirror_connections,
    mirror_footpaths,
    scan,
    unmirror_legs,
)
from backend.planner.rows import (
    render_legs,
    render_no_arrival,
    render_no_route,
    render_no_stop,
    render_same_stop,
    render_walk,
)
from backend.retrieve import Row
from backend.schedules import requested_date
from backend.timetable import (
    gtfs_stamp,
    load_footpaths,
    load_routes,
    load_service_day,
    load_stops,
    place_on_service_day,
    service_date_at,
    service_seconds,
)
from data.schema import connect

# The longest trip offered on foot alone
MAX_TRIP_WALK_SECONDS = 60 * 60


def parse_clock(text: str) -> int | None:
    """Turns a classifier clock string into seconds since midnight.

    Args:
        text: A clock time like "10:17 PM".

    Returns:
        Seconds since midnight, or None.
    """
    try:
        moment = datetime.strptime(text, "%I:%M %p")
    except ValueError:
        return None
    return moment.hour * 3600 + moment.minute * 60


def deadline_moment(deadline: str, day: str | None, now: datetime) -> tuple | None:
    """Places a deadline clock time on its service day.

    Args:
        deadline: The classifier's clock string ("10:17 PM").
        day: The parsed day word, or None.
        now: The time of the query.

    Returns:
        Tuple of (service_date, deadline_seconds) or None.
    """
    clock_seconds = parse_clock(deadline)
    if clock_seconds is None:
        return None

    # The calendar date: named day, today if still ahead, else tomorrow
    if day:
        target = date.fromisoformat(requested_date(day, now))
    elif clock_seconds > now.hour * 3600 + now.minute * 60:
        target = now.date()
    else:
        target = now.date() + timedelta(days=1)

    return place_on_service_day(target, clock_seconds)


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

    # The query has to name both ends
    if not parsed["origin"] or not parsed["destination"]:
        return []

    # Stop names and coordinates
    names, children, parents, positions = load_stops(gtfs_stamp())

    # Match the endpoints, origin first
    connection = connect()
    with connection.cursor() as cursor:
        origin = resolve_endpoint(cursor, parsed["origin"], names, children, positions)
        destination = None
        if origin is not None:
            destination = resolve_endpoint(
                cursor,
                parsed["destination"],
                names,
                children,
                positions,
                origin["point"],
            )
    if origin is None or destination is None:
        return []

    # The same station on both ends
    if origin["stations"] & destination["stations"]:
        return render_same_stop(retrieved_at)

    # The current moment in service time
    now_date = service_date_at(now)
    now_seconds = service_seconds(now) + now.second

    # The service day: backward from a deadline, else forward
    deadline = None
    if parsed["deadline"]:
        placed = deadline_moment(parsed["deadline"], parsed["day"], now)
        if placed is None:
            return []
        service_date, deadline = placed
    elif parsed["day"]:
        # A named day plans that date around the current time
        service_date = date.fromisoformat(requested_date(parsed["day"], now))
        depart_seconds = now.hour * 3600 + now.minute * 60
    else:
        service_date = now_date
        depart_seconds = now_seconds

    origin_walks = origin["walks"]
    destination_walks = destination["walks"]

    # A ride needs a stop within reach of both ends
    best_stop = None
    mirrored = deadline is not None
    if origin_walks and destination_walks:
        stamp = gtfs_stamp()
        routes = load_routes(stamp)
        footpaths = load_footpaths(stamp)
        trips, connections = load_service_day(service_date, stamp)

        # A deadline scans backward from the destination
        if deadline is not None:
            sources = {}
            for platform, walk_seconds in destination_walks.items():
                sources[platform] = -deadline + walk_seconds
            best_stop, earliest, arrived_via, boarded = scan(
                mirror_connections(connections),
                mirror_footpaths(footpaths),
                sources,
                origin_walks,
            )
        else:
            sources = {}
            for platform, walk_seconds in origin_walks.items():
                sources[platform] = depart_seconds + walk_seconds
            best_stop, earliest, arrived_via, boarded = scan(
                connections, footpaths, sources, destination_walks
            )

            # Rescan backward so the leave is the latest for the same arrival
            if best_stop is not None:
                arrive_by = earliest[best_stop] + destination_walks[best_stop]
                sources = {}
                for platform, walk_seconds in destination_walks.items():
                    sources[platform] = -arrive_by + walk_seconds
                best_stop, earliest, arrived_via, boarded = scan(
                    mirror_connections(connections),
                    mirror_footpaths(footpaths),
                    sources,
                    origin_walks,
                )
                mirrored = True

    # A leave time already in the past is not makeable
    if deadline is not None and best_stop is not None:
        leave_seconds = -earliest[best_stop] - origin_walks[best_stop]
        if service_date == now_date and leave_seconds < now_seconds:
            best_stop = None

    # The ridden answer, when the scan found one
    legs = []
    if best_stop is not None:
        legs = build_legs(best_stop, earliest, arrived_via, boarded)
        if mirrored:
            legs = unmirror_legs(legs)

    # How long it takes to just walk there
    direct_seconds = walk_between(origin["point"], destination["point"])

    # Compare walking against the ride
    beats_riding = True
    if legs:
        _, _, trip_depart, trip_arrive = trip_times(legs, origin, destination)
        if deadline is not None:
            beats_riding = deadline - direct_seconds >= trip_depart
        else:
            beats_riding = depart_seconds + direct_seconds <= trip_arrive

    # Check if walking won and is not too long
    if beats_riding and direct_seconds <= MAX_TRIP_WALK_SECONDS:
        if deadline is not None:
            leaves = deadline - direct_seconds
        else:
            leaves = depart_seconds

        # A walk that starts in the past is not makeable
        if service_date != now_date or leaves >= now_seconds:
            return render_walk(
                origin,
                destination,
                service_date,
                leaves,
                direct_seconds,
                retrieved_at,
                deadline,
            )

    # No stop near one of the ends
    if not legs:
        if not origin_walks:
            return render_no_stop(origin, retrieved_at)
        if not destination_walks:
            return render_no_stop(destination, retrieved_at)
        if deadline is not None:
            return render_no_arrival(
                origin, destination, service_date, deadline, retrieved_at
            )
        return render_no_route(
            origin, destination, service_date, depart_seconds, retrieved_at
        )

    return render_legs(
        legs,
        service_date,
        origin,
        destination,
        names,
        parents,
        routes,
        trips,
        retrieved_at,
        deadline,
    )


if __name__ == "__main__":
    from backend.classify import classify

    query = sys.argv[1]
    parsed = classify(query)
    for chunk_id, kind, text, metadata, distance in plan_trip(query, parsed):
        print(f"{chunk_id} {text}")
