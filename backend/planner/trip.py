"""Plan A-to-B transit trips by scanning the day's GTFS timetable."""

import re
import sys
from datetime import date, datetime, timedelta, timezone

from backend.assistant.parse import ParsedQuery
from backend.core.clock import moment_at, now_in_boston, parse_clock
from backend.geo.geocode import Lookup
from backend.planner.ends import resolve_endpoint, trip_times, walk_between
from backend.planner.days import load_service_day
from backend.planner.legs import build_legs, mirror_footpaths, scan, unmirror_legs
from backend.planner.rows import (
    render_legs,
    render_no_arrival,
    render_no_end,
    render_no_route,
    render_no_stop,
    render_none,
    render_same_stop,
    render_unfound,
    render_walk,
)
from backend.assistant.retrieve import Row
from backend.mbta.schedules import WEEKDAYS, requested_date, spoken_day
from backend.planner.timetable import (
    SERVICE_ROLLOVER_HOUR,
    gtfs_stamp,
    last_service_date,
    load_footpaths,
    load_routes,
    load_stops,
    place_on_service_day,
    service_date_at,
    service_seconds,
)
from backend.core.db import borrow

# The longest trip offered on foot alone
MAX_TRIP_WALK_SECONDS = 60 * 60


def deadline_moment(deadline: str, day: str | None, now: datetime) -> tuple | None:
    """Places a clock time on its service day.

    Args:
        deadline: The clock string.
        day: The parsed day word or date, or None.
        now: The time of the query.

    Returns:
        Tuple of (service_date, seconds) or None.
    """
    clock_seconds = parse_clock(deadline)
    if clock_seconds is None:
        print(f"plan: unreadable time {deadline!r}")
        return None

    if day in (None, "today", "tonight"):
        target = service_date_at(now)
        if clock_seconds < SERVICE_ROLLOVER_HOUR * 3600:
            clock_seconds += 24 * 3600
    else:
        named = date.fromisoformat(requested_date(day, now))
        target, clock_seconds = place_on_service_day(named, clock_seconds)

    # The next time that clock comes round
    if not day or day in WEEKDAYS:
        later = 7 if day else 1
        if moment_at(target, clock_seconds) <= now:
            target += timedelta(days=later)

    return target, clock_seconds


def as_typed(query: str, phrase: str) -> str:
    """Finds a place the reader found as the user wrote it.

    Args:
        query: The user's question.
        phrase: The place in the reader's lowercase words.

    Returns:
        The place with the user's own capitals, or the phrase tidied.
    """
    found = typed_span(query, phrase)
    if found is None:
        return phrase.replace(" ,", ",")
    return query[found[0] : found[1]]


def typed_span(query: str, phrase: str) -> tuple[int, int] | None:
    """Finds where a place the reader found sits in the question.

    Args:
        query: The user's question.
        phrase: The place in the reader's lowercase words.

    Returns:
        Tuple of (start, end) in the question, or None.
    """
    words = [word for word in phrase.split() if word != ","]
    if not words:
        return None
    pattern = r"[\s,.']*".join(re.escape(word) for word in words)
    match = re.search(pattern, query, re.IGNORECASE)
    return match.span() if match else None


def asked_with(query: str, phrase: str, label: str) -> str:
    """Asks the question again with a chosen place in the typed one's spot.

    Args:
        query: The user's question.
        phrase: The place in the reader's lowercase words.
        label: The chosen place.

    Returns:
        The new question.
    """
    found = typed_span(query, phrase)
    if found is None:
        return query
    return query[: found[0]] + label + query[found[1] :]


def unfound(query: str, phrase: str, lookup: Lookup, retrieved_at: str) -> list[Row]:
    """Says one end couldn't be found, offering its choices as new questions.

    Args:
        query: The user's question.
        phrase: The end the reader found.
        lookup: What the place search found.
        retrieved_at: When the plan was computed.

    Returns:
        A single unfound row.
    """
    questions = []
    for choice in lookup["choices"]:
        questions.append(asked_with(query, phrase, choice["label"]))
    return render_unfound(as_typed(query, phrase), lookup, questions, retrieved_at)


def plan_trip(query: str, parsed: ParsedQuery, guess: bool = False) -> list[Row]:
    """Plans the trip a query asks for from the GTFS timetable.

    Args:
        query: The user's question.
        parsed: The classifier's read of the query.
        guess: Whether an unclear place takes its best guess.

    Returns:
        Plan rows shaped like retrieved chunks: a summary, then one row
        per leg. An unfound row when an end is missing, unknown or
        unclear; a no-route row when the scan finds nothing.
    """
    now = now_in_boston()
    retrieved_at = datetime.now(timezone.utc).isoformat()

    # The query has to name both ends
    if not parsed["origin"]:
        return render_no_end(None, retrieved_at)
    if not parsed["destination"]:
        return render_no_end(as_typed(query, parsed["origin"]), retrieved_at)

    # Stop names and coordinates
    names, children, parents, positions = load_stops(gtfs_stamp())

    # Match the endpoints, origin first
    with borrow() as connection, connection.cursor() as cursor:
        origin, lookup = resolve_endpoint(
            cursor, parsed["origin"], names, children, positions, guess=guess
        )
        if origin is None:
            return unfound(query, parsed["origin"], lookup, retrieved_at)
        destination, lookup = resolve_endpoint(
            cursor,
            parsed["destination"],
            names,
            children,
            positions,
            origin["point"],
            guess,
        )
        if destination is None:
            return unfound(query, parsed["destination"], lookup, retrieved_at)

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
    elif parsed.get("leave_at"):
        placed = deadline_moment(parsed["leave_at"], parsed["day"], now)
        if placed is None:
            return []
        service_date, depart_seconds = placed
        if (service_date, depart_seconds) < (now_date, now_seconds):
            service_date, depart_seconds = now_date, now_seconds
    elif parsed["day"]:
        # A named day plans that date around the current time
        service_date = date.fromisoformat(requested_date(parsed["day"], now))
        if service_date == now_date:
            depart_seconds = now_seconds
        else:
            depart_seconds = now.hour * 3600 + now.minute * 60
    else:
        service_date = now_date
        depart_seconds = now_seconds

    # A date past the end of the downloaded timetable
    end = last_service_date(gtfs_stamp())
    if end is not None and service_date > end:
        text = (
            f"The timetable only goes through {spoken_day(end)}, "
            f"so there are no trips for {spoken_day(service_date)} yet."
        )
        return render_none(text, retrieved_at)

    origin_walks = origin["walks"]
    destination_walks = destination["walks"]

    # A ride needs a stop within reach of both ends
    best_stop = None
    mirrored = deadline is not None
    if origin_walks and destination_walks:
        stamp = gtfs_stamp()
        routes = load_routes(stamp)
        footpaths = load_footpaths(stamp)
        day = load_service_day(service_date, stamp)

        # A deadline scans backward from the destination
        if deadline is not None:
            sources = {}
            for platform, walk_seconds in destination_walks.items():
                sources[platform] = -deadline + walk_seconds
            best_stop, earliest, arrived_via, boarded = scan(
                day.backward(min(sources.values())),
                mirror_footpaths(footpaths),
                sources,
                origin_walks,
            )
        else:
            sources = {}
            for platform, walk_seconds in origin_walks.items():
                sources[platform] = depart_seconds + walk_seconds
            best_stop, earliest, arrived_via, boarded = scan(
                day.forward(min(sources.values())), footpaths, sources, destination_walks
            )

            # Rescan backward so the leave is the latest for the same arrival
            if best_stop is not None:
                arrive_by = earliest[best_stop] + destination_walks[best_stop]
                sources = {}
                for platform, walk_seconds in destination_walks.items():
                    sources[platform] = -arrive_by + walk_seconds
                best_stop, earliest, arrived_via, boarded = scan(
                    day.backward(min(sources.values())),
                    mirror_footpaths(footpaths),
                    sources,
                    origin_walks,
                )
                mirrored = True

    # A leave time already in the past is not makeable
    if deadline is not None and best_stop is not None:
        leave_seconds = -earliest[best_stop] - origin_walks[best_stop]
        if (service_date, leave_seconds) < (now_date, now_seconds):
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
        if (service_date, leaves) >= (now_date, now_seconds):
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
        day.trips,
        retrieved_at,
        deadline,
    )


if __name__ == "__main__":
    from backend.assistant.parse import read_question

    query = sys.argv[1]
    parsed = read_question(query)
    for chunk_id, kind, text, metadata, distance in plan_trip(query, parsed):
        print(f"{chunk_id} {text}")
