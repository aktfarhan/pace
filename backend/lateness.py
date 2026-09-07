"""Track how late each line has been running."""

import asyncio
import threading
from collections import defaultdict, deque
from datetime import date, datetime, timedelta
from functools import lru_cache
from typing import TypedDict

import httpx
import psycopg

from backend.mbta import fetch
from backend.timetable import (
    gtfs_stamp,
    load_service_day,
    load_stops,
    service_date_at,
    service_seconds,
)
from data.schema import connect

# Tram, subway and bus
ROUTE_TYPES = "0,1,3"

# The lines the delay model answers for
ROUTES = (
    "Red",
    "Orange",
    "Blue",
    "Green-B",
    "Green-C",
    "Green-D",
    "Green-E",
    "Mattapan",
)

# The line each route is drawn under
FAMILIES = {
    "Red": ("Red",),
    "Orange": ("Orange",),
    "Green": ("Green-B", "Green-C", "Green-D", "Green-E"),
    "Blue": ("Blue",),
    "Mattapan": ("Mattapan",),
}

# Trip prefixes with no schedule behind them
UNSCHEDULED = ("ADDED", "NONREV")

# A train counts as late past this many seconds
LATE_SECONDS = 300

# How far back a reading looks
WINDOW_SECONDS = 900

# How stale a vehicle report may be and still be about now
FRESH_SECONDS = 120

# Too few arrivals to read anything from
THIN_WINDOW = 5

# Too few for a bus route
THIN_BUS_WINDOW = 25

# How long an arrival is remembered
COUNTED_SECONDS = 3600

# How often the fleet is read
POLL_SECONDS = 15

# Every line's readings
READ_READINGS = """
    SELECT route_id, at, late, seen FROM readings
    WHERE route_id = ANY(%s) AND at >= %s AND at < %s ORDER BY at;
"""

# One line's closed window
WRITE_READING = """
    INSERT INTO readings (route_id, at, late, seen) VALUES (%s, %s, %s, %s)
    ON CONFLICT (route_id, at) DO NOTHING;
"""


class Reading(TypedDict):
    """One line's share of late arrivals in 15min."""

    at: str
    share: int
    seen: int


# Each line's arrivals inside the window
_arrivals: dict[str, deque[tuple[int, bool]]] = defaultdict(deque)

# The quarter hour whose reading has been written
_written: datetime | None = None

# The arrivals already counted, so a standing train counts once
_counted: dict[tuple[str, str], int] = {}

# The service day the readings belong to
_day: date | None = None

# Held while the readings are changed or read
_lock = threading.Lock()


@lru_cache(maxsize=2)
def scheduled_arrivals(target: date, scraped_at: float) -> dict[tuple[str, str], int]:
    """Reads when each trip is due at each of its stops.

    Args:
        target: The service date.
        scraped_at: When the GTFS tables were scraped.

    Returns:
        Scheduled arrival seconds, keyed by (trip, station).
    """
    _, connections = load_service_day(target, scraped_at)
    _, _, parents, _ = load_stops(scraped_at)

    timetable = {}
    for connection in connections:
        _, _, arrival_seconds, arrival_stop, trip_id, _, _ = connection

        station = parents.get(arrival_stop, arrival_stop)
        timetable[(trip_id, station)] = arrival_seconds

    return timetable


def _parents() -> dict[str, str]:
    """Reads which station each platform belongs to.

    Returns:
        Platform stop id -> parent station id.
    """
    return load_stops(gtfs_stamp())[2]


def linked(vehicle: dict, name: str) -> str | None:
    """Reads one of a vehicle's related ids.

    Args:
        vehicle: A record from the vehicles feed.
        name: The relationship to read.

    Returns:
        The id, or None where the feed left it out.
    """
    return (vehicle["relationships"].get(name, {}).get("data") or {}).get("id")


def forget(clock: int) -> None:
    """Drops the readings that have fallen out of the window.

    Args:
        clock: Seconds since the service day began.
    """
    edge = clock - WINDOW_SECONDS
    for arrivals in _arrivals.values():
        while arrivals and arrivals[0][0] < edge:
            arrivals.popleft()

    # A train can stand longer than the window, and must not count twice
    stale = clock - COUNTED_SECONDS
    for key, when in list(_counted.items()):
        if when < stale:
            del _counted[key]


def record(now: datetime) -> int:
    """Notes every fresh arrival the fleet is reporting.

    Args:
        now: The local time, with a timezone on it.

    Returns:
        How many arrivals this reading added.
    """
    global _day

    target = service_date_at(now)
    clock = service_seconds(now)
    timetable = scheduled_arrivals(target, gtfs_stamp())
    parents = _parents()

    # The fleet is read before the lock is taken
    standing = []
    for vehicle in fetch("/vehicles", {"filter[route_type]": ROUTE_TYPES})["data"]:
        if vehicle["attributes"]["current_status"] != "STOPPED_AT":
            continue

        # A vehicle can sit reporting the same stop for hours
        reported = datetime.fromisoformat(vehicle["attributes"]["updated_at"])
        if (now - reported).total_seconds() > FRESH_SECONDS:
            continue

        # Just after the 3am rollover, a train can still be on yesterday
        if service_date_at(reported) != target:
            continue

        route_id = linked(vehicle, "route")
        trip_id = linked(vehicle, "trip")
        stop_id = linked(vehicle, "stop")

        # Everything the timetable lookup needs
        if route_id is None or trip_id is None or stop_id is None:
            continue

        # The same two prefixes the training table drops
        if trip_id.startswith(UNSCHEDULED):
            continue

        station = parents.get(stop_id, stop_id)
        due = timetable.get((trip_id, station))
        if due is None:
            continue

        # Timed from when the train stopped
        arrived = service_seconds(reported)
        standing.append(
            (arrived, route_id, (trip_id, station), arrived - due > LATE_SECONDS)
        )

    standing.sort()
    added = 0
    with _lock:
        # Only check todays readings
        if target != _day:
            _day = target
            for arrivals in _arrivals.values():
                arrivals.clear()
            _counted.clear()

        # One reading per arrival
        for arrived, route_id, key, was_late in standing:
            if key in _counted:
                continue
            _counted[key] = arrived
            _arrivals[route_id].append((arrived, was_late))
            added += 1

        forget(clock)

    return added


def tally(route: str) -> tuple[int, int]:
    """Counts a line's arrivals in the window.

    Args:
        route: The line's route id.

    Returns:
        (late, seen).
    """
    with _lock:
        arrivals = list(_arrivals.get(route, ()))

    late = 0
    for _, was_late in arrivals:
        if was_late:
            late += 1

    return late, len(arrivals)


def counts(route: str) -> tuple[int, int] | None:
    """Counts a line's recent arrivals and how many ran late.

    Args:
        route: The line's route id.

    Returns:
        (late, seen), or None where the window is too thin.
    """
    late, seen = tally(route)

    # The floor this route reads against
    floor = THIN_WINDOW if route in ROUTES else THIN_BUS_WINDOW
    if seen < floor:
        return None

    return late, seen


def bucket_of(now: datetime) -> datetime:
    """Rounds a moment down to when it started.

    Args:
        now: Any moment.

    Returns:
        The moment that window began.
    """
    width = WINDOW_SECONDS // 60
    return now.replace(minute=now.minute // width * width, second=0, microsecond=0)


def store(now: datetime) -> int:
    """Writes the quarter hour that has just closed.

    Args:
        now: The moment being polled.

    Returns:
        How many lines had an arrival to write down.
    """
    global _written

    bucket = bucket_of(now)
    if bucket == _written:
        return 0

    # The first poll lands mid window
    if _written is None:
        _written = bucket
        return 0

    # The window counts back from now, which is the last quarter
    closed = bucket - timedelta(seconds=WINDOW_SECONDS)
    rows = []
    for route in ROUTES:
        late, seen = tally(route)

        # A thin branch counts once its line is added up
        if seen:
            rows.append((route, closed, late, seen))

    written = 0
    if rows:
        try:
            with connect() as connection, connection.cursor() as cursor:
                cursor.executemany(WRITE_READING, rows)
            written = len(rows)
        except psycopg.Error as error:
            print(f"lateness: {error}")

    # The window moves either way
    _written = bucket

    return written


def read_series(start: datetime, end: datetime) -> dict[str, list[Reading]]:
    """Reads how each line ran across a stretch of the day.

    Args:
        start: The first moment to read.
        end: The moment to stop at.

    Returns:
        One list of readings per line, oldest first.
    """
    # What is asked for and what is drawn come from one map
    family_of = {}
    for line, routes in FAMILIES.items():
        for route in routes:
            family_of[route] = line

    series: dict[str, list[Reading]] = {line: [] for line in FAMILIES}
    try:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(READ_READINGS, (list(family_of), start, end))
            rows = cursor.fetchall()
    except psycopg.Error as error:
        print(f"lateness: {error}")
        return series

    # A branch counts toward its line
    pooled: dict[tuple[datetime, str], list[int]] = {}
    for route_id, at, late, seen in rows:
        totals = pooled.setdefault((at, family_of[route_id]), [0, 0])
        totals[0] += late
        totals[1] += seen

    # The floor applies to the line
    for (at, line), (late, seen) in sorted(pooled.items()):
        if seen >= THIN_WINDOW:
            series[line].append(
                {"at": at.isoformat(), "share": round(late / seen * 100), "seen": seen}
            )
    return series


async def poll() -> None:
    """Reads the fleet on a timer for as long as the server runs."""
    while True:
        try:
            await asyncio.to_thread(record, datetime.now().astimezone())
            await asyncio.to_thread(store, datetime.now().astimezone())
        except httpx.HTTPError as error:
            print(f"lateness: {error}")
        await asyncio.sleep(POLL_SECONDS)
