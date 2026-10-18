"""Track how late each line has been running."""

import asyncio
import threading
from collections import defaultdict, deque
from datetime import date, datetime, time, timedelta, timezone
from functools import lru_cache
from statistics import median
from typing import TypedDict

import psycopg

from backend.clock import ZONE, in_boston, moment_at, now_in_boston
from backend.lines import LINES, LINE_OF, BRANCH_ROUTES
from backend.mbta import fetch
from backend.timetable import (
    SERVICE_ROLLOVER_HOUR,
    gtfs_stamp,
    load_service_day,
    load_stops,
    service_date_at,
    service_seconds,
)
from data.schema import connect

# Tram, subway, commuter rail and bus
ROUTE_TYPES = "0,1,2,3"

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

# How far back one reading pools those windows
ROLLING_SECONDS = 3600

# Too few pooled arrivals to read a share from
ROLLING_FLOOR = 10

# How far back a thin stretch may keep reaching
ROLLING_CAP = 3 * ROLLING_SECONDS

# How many days go into a typical day
TYPICAL_DAYS = 14

# Too few days to call anything typical
TYPICAL_FLOOR = 2

# How wide a stretch one headway is read from
HEADWAY_REACH = 3600

# How long an arrival is remembered
COUNTED_SECONDS = 3600

# How often the fleet is read
POLL_SECONDS = 15

# How long a saved quarter hour is kept
KEPT_SECONDS = 3600

# A line is resting when the next train is further off than this
RESTING_SECONDS = 900

# Every line's readings
READ_READINGS = """
    SELECT route_id, at, late, seen FROM readings
    WHERE route_id = ANY(%s) AND at >= %s AND at < %s ORDER BY at;
"""

# One line's quarter hour
WRITE_READING = """
    INSERT INTO readings (route_id, at, late, seen) VALUES (%s, %s, %s, %s)
    ON CONFLICT (route_id, at) DO UPDATE SET late = EXCLUDED.late, seen = EXCLUDED.seen;
"""

# Every line's count for the quarter hours
READ_QUARTERS = """
    SELECT route_id, at, late, seen FROM readings WHERE at >= %s AND at <= %s;
"""


# A closed quarter hour and its counts
Quarter = tuple[datetime, int, int]


class Reading(TypedDict):
    """A line or branch's share of late arrivals across the stretch before it."""

    at: str
    share: int
    seen: int
    reach: int


class TypicalReading(Reading):
    """A reading over today from the middle of earlier days."""

    days: int


# Each line's arrivals inside the window
_arrivals: dict[str, deque[tuple[int, bool]]] = defaultdict(deque)

# Each quarter hour's (late, seen) per line
_quarters: dict[datetime, dict[str, list[int]]] = {}

# The quarter hours with counts the database doesn't have yet
_unsaved: set[datetime] = set()

# The quarter hour the last summary line was printed for
_summarized: datetime | None = None

# Arrivals counted since that summary
_added = 0

# Trips seen standing that the timetable doesn't know
_skipped: set[str] = set()

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
        now: The time, with a timezone on it.

    Returns:
        How many arrivals this reading added.
    """
    global _day, _added

    target = service_date_at(now)
    clock = service_seconds(now)
    timetable = scheduled_arrivals(target, gtfs_stamp())
    parents = _parents()

    # The fleet is read before the lock is taken
    standing = []
    skipped = set()
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
            skipped.add(trip_id)
            continue

        # Timed from when the train stopped
        arrived = service_seconds(reported)
        standing.append(
            (
                arrived,
                route_id,
                (trip_id, station),
                arrived - due > LATE_SECONDS,
                bucket_of(in_boston(reported)),
            )
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
        for arrived, route_id, key, was_late, quarter in standing:
            if key in _counted:
                continue
            _counted[key] = arrived
            _arrivals[route_id].append((arrived, was_late))
            added += 1

            # The quarter hour it arrived in
            if route_id in LINE_OF:
                totals = _quarters.setdefault(quarter, {}).setdefault(route_id, [0, 0])
                totals[0] += was_late
                totals[1] += 1
                _unsaved.add(quarter)

        _added += added
        _skipped.update(skipped)
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


def write(rows: list[tuple[str, datetime, int, int]]) -> bool:
    """Writes quarter hour counts, replacing any earlier count of the same quarter.

    Args:
        rows: (route, quarter start, late, seen) per line.

    Returns:
        Whether the database took them.
    """
    try:
        with connect() as connection, connection.cursor() as cursor:
            cursor.executemany(WRITE_READING, rows)
    except psycopg.Error as error:
        print(f"lateness: {error}")
        return False
    return True


def summarize(now: datetime) -> None:
    """Prints one line per quarter hour on what the poller counted.

    Args:
        now: The moment being polled.
    """
    global _summarized, _added

    quarter = bucket_of(now)
    if quarter == _summarized:
        return

    with _lock:
        added = _added
        skipped = len(_skipped)
        _added = 0
        _skipped.clear()

    # The first quarter began before the server
    if _summarized is not None:
        print(
            f"lateness: {in_boston(_summarized):%H:%M} quarter: "
            f"{added} arrivals counted, "
            f"{skipped} trains skipped (trip not in the timetable)"
        )
    _summarized = quarter


def store(now: datetime) -> int:
    """Writes every quarter hour that has closed with new arrivals in it.

    Args:
        now: The moment being polled.

    Returns:
        How many line counts were written.
    """
    summarize(now)
    opened = bucket_of(now)

    # Only arrivals inside each closed quarter count toward it
    with _lock:
        closed = sorted(at for at in _unsaved if at < opened)
        taken = {
            at: {route: list(totals) for route, totals in _quarters[at].items()}
            for at in closed
        }

    rows = []
    for at, routes in taken.items():
        for route, (late, seen) in routes.items():
            rows.append((route, at, late, seen))

    written = 0
    if rows and write(rows):
        written = len(rows)

        # Saved, unless an arrival joined it since
        with _lock:
            for at, routes in taken.items():
                current = {
                    route: list(totals) for route, totals in _quarters[at].items()
                }
                if current == routes:
                    _unsaved.discard(at)

        # The day's readings have gained a quarter
        read_series.cache_clear()

    # Saved quarters stay an hour
    edge = opened - timedelta(seconds=KEPT_SECONDS)
    with _lock:
        for at in list(_quarters):
            if at < edge and at not in _unsaved:
                del _quarters[at]

    return written


def save_open() -> int:
    """Writes every unsaved quarter hour.

    Returns:
        How many line counts were written.
    """
    with _lock:
        rows = []
        for at in sorted(_unsaved):
            for route, (late, seen) in _quarters[at].items():
                rows.append((route, at, late, seen))

    if rows and write(rows):
        return len(rows)
    return 0


def resume(now: datetime) -> int:
    """Reads back the recent quarter hours saved.

    Args:
        now: The time the server started.

    Returns:
        How many line counts were read back.
    """
    opened = bucket_of(now)

    # The last hour
    edge = opened - timedelta(seconds=KEPT_SECONDS)
    try:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(READ_QUARTERS, (edge, opened))
            rows = cursor.fetchall()
    except psycopg.Error as error:
        print(f"lateness: {error}")
        return 0

    # New arrivals add to the saved counts
    with _lock:
        for route_id, at, late, seen in rows:
            _quarters.setdefault(in_boston(at), {})[route_id] = [late, seen]

    return len(rows)


def keys_for(route_id: str) -> list[str]:
    """Finds where a route's arrivals get counted.

    Args:
        route_id: The route the arrivals were seen on.

    Returns:
        Its line, and the route.
    """
    keys = [LINE_OF[route_id]]

    # A branch also counts on its own
    if route_id in BRANCH_ROUTES:
        keys.append(route_id)

    return keys


def first_departures(target: date, after: int, scraped_at: float) -> dict[str, int]:
    """Finds each line's first departure at or after a time.

    Args:
        target: The service date.
        after: Seconds into that day to look on from.
        scraped_at: When the GTFS tables were scraped.

    Returns:
        Seconds into the day of the earliest departure, per line and per branch.
    """
    trips, connections = load_service_day(target, scraped_at)

    soonest: dict[str, int] = {}
    for departure, _, _, _, trip_id, _, _ in connections:
        # Already gone
        if departure < after:
            continue

        trip = trips.get(trip_id)

        # Buses and anything that is not a line
        if trip is None or trip[0] not in LINE_OF:
            continue

        for key in keys_for(trip[0]):
            if key not in soonest or departure < soonest[key]:
                soonest[key] = departure

    return soonest


@lru_cache(maxsize=2)
def read_resumes(edge: datetime, scraped_at: float) -> dict[str, str]:
    """Reads when each lines next train is booked.

    Args:
        edge: The quarter hour to look on from.
        scraped_at: When the GTFS tables were scraped.

    Returns:
        When the next train is booked, per line and per branch.
    """
    target = service_date_at(edge)
    found = {
        key: moment_at(target, seconds)
        for key, seconds in first_departures(
            target, service_seconds(edge), scraped_at
        ).items()
    }

    # Between the last train and the 3 AM rollover
    every = set(LINE_OF.values()) | BRANCH_ROUTES
    if not every <= found.keys():
        later = target + timedelta(days=1)
        for key, seconds in first_departures(later, 0, scraped_at).items():
            found.setdefault(key, moment_at(later, seconds))

    return {key: at.astimezone(timezone.utc).isoformat() for key, at in found.items()}


@lru_cache(maxsize=3)
def line_spans(target: date, scraped_at: float) -> dict[str, list[tuple[int, int]]]:
    """Reads when each of a line's trips sets off and finishes.

    Args:
        target: The service date.
        scraped_at: When the GTFS tables were scraped.

    Returns:
        (first departure, last arrival) seconds per trip.
    """
    trips, connections = load_service_day(target, scraped_at)

    spans: dict[str, list[int]] = {}
    for departure, _, arrival, _, trip_id, _, _ in connections:
        trip = trips.get(trip_id)

        # Buses and anything that is not a line
        if trip is None or trip[0] not in LINE_OF:
            continue

        span = spans.get(trip_id)
        if span is None:
            spans[trip_id] = [departure, arrival]
        else:
            span[0] = min(span[0], departure)
            span[1] = max(span[1], arrival)

    by_line: dict[str, list[tuple[int, int]]] = {}
    for trip_id, (start, end) in spans.items():
        by_line.setdefault(LINE_OF[trips[trip_id][0]], []).append((start, end))

    for ordered in by_line.values():
        ordered.sort()
    return by_line


def read_resting(now: datetime) -> dict[str, str]:
    """Finds the lines with no train running, and when each starts again.

    Args:
        now: The time.

    Returns:
        When the next train sets off.
    """
    stamp = gtfs_stamp()
    target = service_date_at(now)
    clock = service_seconds(now) + now.second
    today = line_spans(target, stamp)

    resting = {}
    for line_id, _, _, _ in LINES:
        spans = today.get(line_id, [])

        # A trip under way means the line is running
        if any(start <= clock <= end for start, end in spans):
            continue

        # The next trip today, else the first one tomorrow
        ahead = [start for start, _ in spans if start > clock]
        if ahead:
            back = moment_at(target, min(ahead))
        else:
            later = target + timedelta(days=1)
            tomorrow = line_spans(later, stamp).get(line_id)

            # No trips at all is a gap in the timetable
            if not tomorrow:
                continue
            back = moment_at(later, tomorrow[0][0])

        # A short gap between trains is not a line at rest
        if (back - now).total_seconds() > RESTING_SECONDS:
            resting[line_id] = back.isoformat()

    return resting


@lru_cache(maxsize=2)
def read_headways(target: date, hour: int, scraped_at: float) -> dict[str, int]:
    """Reads how often each line is scheduled to come by around an hour.

    Args:
        target: The service date.
        hour: The hour of the service day to read.
        scraped_at: When the GTFS tables were scraped.

    Returns:
        Whole minutes between trains, per line and per branch.
    """
    trips, connections = load_service_day(target, scraped_at)
    _, _, parents, _ = load_stops(scraped_at)

    # Trains are read an hour either side of this
    middle = hour * 3600

    # Trains booked into each stop
    booked: dict[tuple[str, str, str], list[int]] = {}
    for _, _, arrival_seconds, arrival_stop, trip_id, _, _ in connections:
        if abs(arrival_seconds - middle) > HEADWAY_REACH:
            continue

        trip = trips.get(trip_id)

        # Buses and anything that is not a line
        if trip is None or trip[0] not in LINE_OF:
            continue

        # A platform counts under its station
        station = parents.get(arrival_stop, arrival_stop)
        for key in keys_for(trip[0]):
            booked.setdefault((key, station, trip[1]), []).append(arrival_seconds)

    # The busiest stop is used
    busiest: dict[str, list[int]] = {}
    for (key, _, _), times in booked.items():
        if len(times) > len(busiest.get(key, [])):
            busiest[key] = times

    headways: dict[str, int] = {}
    for key, times in busiest.items():
        times.sort()

        # The wait between one train and the next
        gaps = [later - sooner for sooner, later in zip(times, times[1:])]

        # One train on its own shows no gap
        if not gaps:
            continue

        # One long gap would drag a mean
        headways[key] = max(round(median(gaps) / 60), 1)

    return headways


def rolling(quarters: list[Quarter]) -> list[Reading]:
    """Counts the arrivals behind each quarter hour.

    Args:
        quarters: The quarter hours to read, oldest first.

    Returns:
        One reading per quarter hour with enough arrivals.
    """
    # A quarter hour alone is too thin
    span = timedelta(seconds=ROLLING_SECONDS)
    cap = timedelta(seconds=ROLLING_CAP)

    readings: list[Reading] = []
    for index, (at, _, _) in enumerate(quarters):
        # What the quarters behind this one add up to
        late = 0
        seen = 0
        reach = timedelta()

        for back in range(index, -1, -1):
            back_at, back_late, back_seen = quarters[back]
            behind = at - back_at

            # Past the span, only a thin stretch keeps reaching
            if behind >= span and seen >= ROLLING_FLOOR:
                break

            if behind >= cap:
                break

            late += back_late
            seen += back_seen

            # How far this one ended up reaching
            reach = behind

        # A thin stretch means nothing worth drawing
        if seen < ROLLING_FLOOR:
            continue

        readings.append(
            {
                "at": at.isoformat(),
                "share": round(late / seen * 100),
                "seen": seen,
                "reach": round((reach.total_seconds() + WINDOW_SECONDS) / 60),
            }
        )

    return readings


def empty_series() -> dict[str, list[Reading]]:
    """Builds a reading list for every line and branch.

    Returns:
        One empty list per line and per branch.
    """
    series: dict[str, list[Reading]] = {line_id: [] for line_id, _, _, _ in LINES}
    series.update({route: [] for route in sorted(BRANCH_ROUTES)})
    return series


@lru_cache(maxsize=2)
def read_typical(began: datetime, edge: datetime) -> dict[str, list[TypicalReading]]:
    """Reads the share each line typically runs at, by time of day.

    Args:
        began: When today's service day started.
        edge: The quarter hour the readings run up to.

    Returns:
        One list of readings per line and per branch, laid over today's clock.
    """
    typical: dict[str, list[TypicalReading]] = {key: [] for key in empty_series()}
    start = began - timedelta(days=TYPICAL_DAYS)
    try:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(READ_READINGS, (list(LINE_OF), start, began))
            rows = cursor.fetchall()
    except psycopg.Error as error:
        print(f"lateness: {error}")
        return typical

    # A branch counts toward its line
    pooled: dict[tuple[date, str, datetime], list[int]] = {}
    for route_id, at, late, seen in rows:
        at = at.astimezone(ZONE)
        served = service_date_at(at)
        for key in keys_for(route_id):
            totals = pooled.setdefault((served, key, at), [0, 0])
            totals[0] += late
            totals[1] += seen

    # Each earlier day's quarter hours
    quarters: dict[tuple[date, str], list[Quarter]] = {}
    for (served, key, at), (late, seen) in sorted(pooled.items()):
        quarters.setdefault((served, key), []).append((at, late, seen))

    # What each day looked like at that minute
    stacked: dict[tuple[str, int], list[Reading]] = {}
    for (served, key), day in quarters.items():
        opened = datetime.combine(served, time(SERVICE_ROLLOVER_HOUR), ZONE)
        for reading in rolling(day):
            minute = round(
                (datetime.fromisoformat(reading["at"]) - opened).total_seconds() / 60
            )
            stacked.setdefault((key, minute), []).append(reading)

    # The middle day, laid back over today
    for (key, minute), stood in sorted(stacked.items()):
        if len(stood) < TYPICAL_FLOOR:
            continue

        at = began + timedelta(minutes=minute)

        # Today has not reached this time yet
        if at >= edge:
            continue

        typical[key].append(
            {
                "at": at.astimezone(timezone.utc).isoformat(),
                "share": round(median(x["share"] for x in stood)),
                "seen": sum(x["seen"] for x in stood),
                "reach": round(sum(x["reach"] for x in stood) / len(stood)),
                "days": len(stood),
            }
        )

    return typical


@lru_cache(maxsize=2)
def read_series(start: datetime, end: datetime) -> dict[str, list[Reading]]:
    """Reads how each line and branch ran across a stretch of the day.

    Args:
        start: The first moment to read.
        end: The moment to stop at.

    Returns:
        One list of readings per line and per branch, oldest first.
    """
    series = empty_series()
    try:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(READ_READINGS, (list(LINE_OF), start, end))
            rows = cursor.fetchall()
    except psycopg.Error as error:
        print(f"lateness: {error}")
        return series

    # A branch counts toward its line, and itself
    pooled: dict[tuple[datetime, str], list[int]] = {}
    for route_id, at, late, seen in rows:
        for key in keys_for(route_id):
            totals = pooled.setdefault((at, key), [0, 0])
            totals[0] += late
            totals[1] += seen

    # Each line and branch, oldest first
    ordered: dict[str, list[Quarter]] = {}
    for (at, key), (late, seen) in sorted(pooled.items()):
        ordered.setdefault(key, []).append((at, late, seen))

    for key, quarters in ordered.items():
        series[key] = rolling(quarters)
    return series


async def poll() -> None:
    """Reads the fleet on a timer for as long as the server runs."""
    while True:
        try:
            await asyncio.to_thread(record, now_in_boston())
            await asyncio.to_thread(store, now_in_boston())
        except Exception as error:
            print(f"lateness: {type(error).__name__}: {error}")
        await asyncio.sleep(POLL_SECONDS)
