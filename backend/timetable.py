"""Load the GTFS timetable tables for one service day."""

import csv
from datetime import date
from pathlib import Path

GTFS_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "gtfs"

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


def load_stops() -> tuple[dict, dict, dict]:
    """Loads stop names and the station-platform structure.

    Returns:
        Tuple of (names, children, parents): stop_id -> name for every
        stop, parent station id -> boarding platform ids, and platform
        id -> parent station id.
    """
    names = {}
    children = {}
    parents = {}
    for row in read_table("stops.txt"):
        # Every stop keeps its display name
        names[row["stop_id"]] = row["stop_name"]

        # Boarding platforms link to their station
        if row["parent_station"] and row["location_type"] in ("", "0"):
            children.setdefault(row["parent_station"], []).append(row["stop_id"])
            parents[row["stop_id"]] = row["parent_station"]
    return names, children, parents


def load_routes() -> dict:
    """Loads the label fields for every route.

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


def load_footpaths() -> dict:
    """Builds the walking-transfer map from transfers.txt.

    Returns:
        stop_id -> list of (to_stop_id, walk_seconds).
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
    return footpaths
