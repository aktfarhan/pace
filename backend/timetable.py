"""Load the GTFS timetable tables and read which service day is running."""

import csv
from datetime import date, datetime, timedelta
from functools import lru_cache
from pathlib import Path

INFINITY = float("inf")

GTFS_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "gtfs"

# Service days held in memory at once
CACHED_DAYS = 2

# Before this hour, "today" is still yesterday's MBTA service day
SERVICE_ROLLOVER_HOUR = 3

# Tram, subway and commuter rail
STATION_ROUTE_TYPES = ("0", "1", "2")

WEEKDAY_COLUMNS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


def parse_gtfs_time(text: str) -> int:
    """Turns a GTFS clock string into seconds.

    Args:
        text: "HH:MM:SS", where hours pass 24.

    Returns:
        Seconds since midnight.
    """
    hours, minutes, seconds = text.split(":")
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds)


def read_table(name: str) -> list[dict[str, str]]:
    """Reads one GTFS table into dict rows.

    Args:
        name: The table's filename ("trips.txt").

    Returns:
        One dict per row, keyed by the header columns.
    """
    # Strip BOM with utf-8-sig
    with (GTFS_DIR / name).open(encoding="utf-8-sig", newline="") as table_file:
        return list(csv.DictReader(table_file))


def place_on_service_day(target: date, clock_seconds: int) -> tuple[date, int]:
    """Places a calendar date and clock time on the service day.

    Args:
        target: The calendar date the clock time falls on.
        clock_seconds: Seconds since midnight on that date.

    Returns:
        Tuple of (service date, seconds since that service day began).
    """
    if clock_seconds < SERVICE_ROLLOVER_HOUR * 3600:
        return target - timedelta(days=1), clock_seconds + 24 * 3600
    return target, clock_seconds


def service_date_at(now: datetime) -> date:
    """Reads which service day is running at a local moment.

    Args:
        now: The local time.

    Returns:
        The date whose service is running.
    """
    return place_on_service_day(now.date(), now.hour * 3600 + now.minute * 60)[0]


def service_seconds(now: datetime) -> int:
    """Reads the service clock at a moment.

    Args:
        now: The local time.

    Returns:
        Seconds since the service day began.
    """
    return place_on_service_day(now.date(), now.hour * 3600 + now.minute * 60)[1]


def active_service_ids(target: date) -> set[str]:
    """Finds the service ids running on a date.

    Args:
        target: The service date.

    Returns:
        Service ids active that day: the weekly calendar filtered to
        its date window, then calendar_dates exceptions applied.
    """
    stamp = target.strftime("%Y%m%d")
    weekday = WEEKDAY_COLUMNS[target.weekday()]

    # The weekly pattern, inside its date window
    active = set()
    for row in read_table("calendar.txt"):
        if row[weekday] == "1" and row["start_date"] <= stamp <= row["end_date"]:
            active.add(row["service_id"])

    # Single-date exceptions: 1 adds service, 2 removes it
    for row in read_table("calendar_dates.txt"):
        if row["date"] != stamp:
            continue
        if row["exception_type"] == "1":
            active.add(row["service_id"])
        else:
            active.discard(row["service_id"])
    return active


@lru_cache(maxsize=1)
def load_stops(scraped_at: float) -> tuple[dict, dict, dict, dict]:
    """Loads stop names, the station-platform structure, and coordinates.

    Args:
        scraped_at: When the tables were scraped.

    Returns:
        Tuple of (names, children, parents, positions): stop_id -> name
        for every stop, parent station id -> boarding platform ids,
        platform id -> parent station id, and stop_id -> (lat, lon).
    """
    names = {}
    children = {}
    parents = {}
    positions = {}
    for row in read_table("stops.txt"):
        # Every stop keeps its display name
        names[row["stop_id"]] = row["stop_name"]

        # Location type 1 is a station, 3 is a pathway node
        if row["location_type"] not in ("", "0"):
            continue

        positions[row["stop_id"]] = (float(row["stop_lat"]), float(row["stop_lon"]))

        # Boarding platforms link to their station
        if row["parent_station"]:
            children.setdefault(row["parent_station"], []).append(row["stop_id"])
            parents[row["stop_id"]] = row["parent_station"]
    return names, children, parents, positions


@lru_cache(maxsize=1)
def load_routes(scraped_at: float) -> dict:
    """Loads the label fields for every route.

    Args:
        scraped_at: When the tables were scraped.

    Returns:
        route_id -> (short_name, long_name, route_type).
    """
    routes = {}
    for row in read_table("routes.txt"):
        # Three fields for a route label
        routes[row["route_id"]] = (
            row["route_short_name"],
            row["route_long_name"],
            int(row["route_type"]),
        )
    return routes


@lru_cache(maxsize=1)
def load_route_order(scraped_at: float) -> dict:
    """Loads the MBTA's rank for every rail route.

    Args:
        scraped_at: When the tables were scraped.

    Returns:
        route_id -> sort order, lowest first.
    """
    order = {}
    for row in read_table("routes.txt"):
        if row["route_type"] in STATION_ROUTE_TYPES:
            order[row["route_id"]] = int(row["route_sort_order"])
    return order


def load_trips(services: set[str]) -> dict:
    """Loads the trips running on the target date.

    Args:
        services: The date's active service ids.

    Returns:
        trip_id -> (route_id, headsign) for the active trips.
    """
    trips = {}
    for row in read_table("trips.txt"):
        # Keep a trip only when its service runs that day
        if row["service_id"] in services:
            trips[row["trip_id"]] = (row["route_id"], row["trip_headsign"])
    return trips


def load_connections(trips: dict) -> list[tuple]:
    """Builds the day's connections from stop_times.

    Args:
        trips: The date's active trips.

    Returns:
        One connection per consecutive stop pair on an active trip, as
        (departure_seconds, departure_stop, arrival_seconds,
        arrival_stop, trip_id, boardable, alightable), sorted by
        departure time.
    """
    # Column indexes from the header
    stop_times = {}
    stop_times_path = GTFS_DIR / "stop_times.txt"
    with stop_times_path.open(encoding="utf-8-sig", newline="") as table_file:
        reader = csv.reader(table_file)
        header = next(reader)
        trip_column = header.index("trip_id")
        arrival_column = header.index("arrival_time")
        departure_column = header.index("departure_time")
        stop_column = header.index("stop_id")
        sequence_column = header.index("stop_sequence")
        pickup_column = header.index("pickup_type")
        drop_off_column = header.index("drop_off_type")

        # Keep the active trips' rows, grouped by trip
        for row in reader:
            trip_id = row[trip_column]
            if trip_id not in trips:
                continue

            # (sequence, departure, arrival, stop, boardable, alightable)
            stop_times.setdefault(trip_id, []).append(
                (
                    int(row[sequence_column]),
                    parse_gtfs_time(row[departure_column]),
                    parse_gtfs_time(row[arrival_column]),
                    row[stop_column],
                    row[pickup_column] != "1",
                    row[drop_off_column] != "1",
                )
            )

    # Build connections: pair each trip's consecutive stops
    connections = []
    for trip_id, trip_stops in stop_times.items():
        # Stops in riding order
        trip_stops.sort()
        for index in range(len(trip_stops) - 1):
            _, departure_seconds, _, departure_stop, boardable, _ = trip_stops[index]
            _, _, arrival_seconds, arrival_stop, _, alightable = trip_stops[index + 1]
            connections.append(
                (
                    departure_seconds,
                    departure_stop,
                    arrival_seconds,
                    arrival_stop,
                    trip_id,
                    boardable,
                    alightable,
                )
            )

    # Sort departures in time order
    connections.sort(key=lambda connection: connection[0])
    return connections


def gtfs_stamp() -> float:
    """Reads when the GTFS tables were last scraped.

    Returns:
        The modification time of stop_times.txt.
    """
    return (GTFS_DIR / "stop_times.txt").stat().st_mtime


@lru_cache(maxsize=CACHED_DAYS)
def load_service_day(target: date, scraped_at: float) -> tuple[dict, list]:
    """Loads the trips and connections running on a date.

    Args:
        target: The service date.
        scraped_at: When the tables were scraped.

    Returns:
        Tuple of (trips, connections).
    """
    services = active_service_ids(target)
    trips = load_trips(services)
    return trips, load_connections(trips)


def close_footpaths(footpaths: dict) -> dict:
    """Expands each stop's walks to every stop it can reach.

    Args:
        footpaths: stop_id -> list of (to_stop_id, walk_seconds).

    Returns:
        One shortest walk per reachable stop.
    """
    # Set of every walk start or end stop
    stops = set(footpaths)
    for walks in footpaths.values():
        for to_stop, _ in walks:
            stops.add(to_stop)

    closed = {}
    for start in stops:
        # The shortest walk to every other stop this stop reaches
        shortest = {start: 0}
        pending = {start}
        while pending:
            # The closest stop not checked yet
            stop = min(pending, key=lambda candidate: shortest[candidate])
            pending.discard(stop)

            # Add each walk to the time so far
            for to_stop, walk_seconds in footpaths.get(stop, []):
                arrival = shortest[stop] + walk_seconds

                # Keep it only when it beats the time already found
                if arrival < shortest.get(to_stop, INFINITY):
                    shortest[to_stop] = arrival
                    pending.add(to_stop)

        # The reachable stops as a list
        walks = []
        for to_stop, walk_seconds in shortest.items():
            if to_stop != start:
                walks.append((to_stop, walk_seconds))

        # A stop that goes nowhere gets no entry
        if walks:
            closed[start] = walks
    return closed


@lru_cache(maxsize=1)
def load_footpaths(scraped_at: float) -> dict:
    """Builds the walking-transfer map from transfers.txt.

    Args:
        scraped_at: When the tables were scraped.

    Returns:
        stop_id -> list of (to_stop_id, walk_seconds),
        one per stop the walks reach.
    """
    footpaths = {}
    for row in read_table("transfers.txt"):
        # Type 3 marks a transfer that is not possible
        if row["transfer_type"] == "3":
            continue
        walk_seconds = int(row["min_transfer_time"] or 0)
        footpaths.setdefault(row["from_stop_id"], []).append(
            (row["to_stop_id"], walk_seconds)
        )

    # One entry for every stop reachable
    return close_footpaths(footpaths)


def warm() -> None:
    """Loads every cached table."""
    stamp = gtfs_stamp()
    load_stops(stamp)
    load_routes(stamp)
    load_footpaths(stamp)
    load_service_day(service_date_at(datetime.now()), stamp)
