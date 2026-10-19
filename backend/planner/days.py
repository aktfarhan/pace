"""Store each service day as number columns, one ready-made file per schedule pattern."""

import csv
import hashlib
import os
import sys
import threading
from bisect import bisect_left
from collections.abc import Iterator
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas

from backend.core.clock import now_in_boston
from backend.planner.timetable import (
    CACHED_DAYS,
    GTFS_DIR,
    active_service_ids,
    gtfs_stamp,
    last_service_date,
    load_footpaths,
    load_routes,
    load_stops,
    parse_gtfs_time,
    service_date_at,
)

# Where the ready-made days are kept
DAYS_DIR = GTFS_DIR / "days"

# Rows of stop_times read at once
READ_ROWS = 200_000

# Connections turned into Python values at once
CHUNK = 2048

# The stop_times columns a day is built from
STOP_TIME_COLUMNS = [
    "trip_id",
    "arrival_time",
    "departure_time",
    "stop_id",
    "stop_sequence",
    "pickup_type",
    "drop_off_type",
]

# Held while day files are written
_building = threading.Lock()


class Day:
    """One schedule pattern's connections, as columns sorted by departure."""

    def __init__(self, columns: dict[str, np.ndarray]):
        """Unpacks a day file.

        Args:
            columns: The arrays a day file holds.
        """
        self.departures = columns["departures"]
        self.arrivals = columns["arrivals"]
        self.from_stops = columns["from_stops"]
        self.to_stops = columns["to_stops"]
        self.trip_of = columns["trip_of"]
        self.boardable = columns["boardable"]
        self.alightable = columns["alightable"]

        # Positions in reversed time, for the backward scan
        self.backward_order = columns["backward_order"]

        # Positions grouped by trip in riding order
        self.trip_order = columns["trip_order"]
        self.trip_starts = columns["trip_starts"]

        # One shared copy of each name
        self.stops = [sys.intern(stop) for stop in unpack(columns["stops"])]
        self.trip_ids = unpack(columns["trip_ids"])
        routes = [sys.intern(route) for route in unpack(columns["routes"])]
        headsigns = [sys.intern(sign) for sign in unpack(columns["headsigns"])]

        # trip_id -> (route_id, headsign), as the tables give it
        self.trips = dict(zip(self.trip_ids, zip(routes, headsigns)))
        self.trip_index = {trip_id: index for index, trip_id in enumerate(self.trip_ids)}

        # Positions kept per set of routes
        self._kept: dict[frozenset, np.ndarray] = {}

    def __len__(self) -> int:
        """Counts the day's connections."""
        return len(self.departures)

    def rows(
        self, positions: np.ndarray | None = None, start: int = 0, mirrored: bool = False
    ) -> Iterator[tuple]:
        """Reads connections as tuples, a chunk at a time.

        Args:
            positions: The connections to read, in order; None reads them all.
            start: How many of them to skip.
            mirrored: Whether to flip each one into reversed time.

        Yields:
            (departure_seconds, departure_stop, arrival_seconds,
            arrival_stop, trip_id, boardable, alightable).
        """
        stops = self.stops
        trip_ids = self.trip_ids
        total = len(self) if positions is None else len(positions)
        for at in range(start, total, CHUNK):
            if positions is None:
                part = slice(at, at + CHUNK)
            else:
                part = positions[at : at + CHUNK]

            departures = self.departures[part]
            arrivals = self.arrivals[part]
            from_stops = map(stops.__getitem__, self.from_stops[part].tolist())
            to_stops = map(stops.__getitem__, self.to_stops[part].tolist())
            trips = map(trip_ids.__getitem__, self.trip_of[part].tolist())
            boardable = self.boardable[part].tolist()
            alightable = self.alightable[part].tolist()

            # Reversed time swaps the ends and negates the clock
            if mirrored:
                yield from zip(
                    (-arrivals).tolist(),
                    to_stops,
                    (-departures).tolist(),
                    from_stops,
                    trips,
                    alightable,
                    boardable,
                )
            else:
                yield from zip(
                    departures.tolist(),
                    from_stops,
                    arrivals.tolist(),
                    to_stops,
                    trips,
                    boardable,
                    alightable,
                )

    def forward(self, after: float) -> Iterator[tuple]:
        """Reads the connections leaving at or after a time.

        Args:
            after: Seconds into the service day.

        Yields:
            Connections sorted by departure.
        """
        start = int(np.searchsorted(self.departures, after, side="left"))
        return self.rows(start=start)

    def backward(self, after: float) -> Iterator[tuple]:
        """Reads the connections in reversed time, from a reversed time on.

        Args:
            after: A negated time, as the backward scan counts.

        Yields:
            Mirrored connections sorted by their negated arrival.
        """
        order = self.backward_order
        start = bisect_left(
            range(len(order)), after, key=lambda at: -int(self.arrivals[order[at]])
        )
        return self.rows(order, start, mirrored=True)

    def kept(self, routes: frozenset) -> np.ndarray:
        """Finds the connections on a set of routes.

        Args:
            routes: The route ids to keep.

        Returns:
            Their positions, in departure order.
        """
        if routes not in self._kept:
            on_route = np.array(
                [self.trips[trip_id][0] in routes for trip_id in self.trip_ids],
                dtype=bool,
            )
            self._kept[routes] = np.flatnonzero(on_route[self.trip_of]).astype(np.int32)
        return self._kept[routes]

    def ridden(self, trip_id: str) -> list[tuple[int, str]]:
        """Reads a trip's arrivals in riding order.

        Args:
            trip_id: The trip.

        Returns:
            (arrival_seconds, arrival_stop) per stop after the first, or empty.
        """
        index = self.trip_index.get(trip_id)
        if index is None:
            return []
        part = self.trip_order[self.trip_starts[index] : self.trip_starts[index + 1]]
        stops = map(self.stops.__getitem__, self.to_stops[part].tolist())
        return list(zip(self.arrivals[part].tolist(), stops))


def pack(words: list[str]) -> np.ndarray:
    """Joins names into one compact array of bytes.

    Args:
        words: The names, none holding a line break.

    Returns:
        The names as UTF-8 bytes, one per line.
    """
    return np.frombuffer("\n".join(words).encode(), dtype=np.uint8)


def unpack(packed: np.ndarray) -> list[str]:
    """Splits packed bytes back into names.

    Args:
        packed: Bytes from pack.

    Returns:
        The names, in order.
    """
    if not len(packed):
        return []
    return packed.tobytes().decode().split("\n")


def pattern_name(services: frozenset) -> str:
    """Names a schedule pattern by the services in it.

    Args:
        services: The service ids running.

    Returns:
        A short name that changes when the services do.
    """
    joined = "\n".join(sorted(services)).encode()
    return hashlib.sha1(joined).hexdigest()[:16]


def day_path(services: frozenset) -> Path:
    """Finds where a pattern's file lives.

    Args:
        services: The service ids running.

    Returns:
        The file's path.
    """
    return DAYS_DIR / f"{pattern_name(services)}.npz"


def read_stop_times(trip_index: dict[str, int]) -> dict[str, np.ndarray]:
    """Reads the rows of stop_times for the given trips into columns.

    Args:
        trip_index: trip_id -> its number, for the trips to keep.

    Returns:
        Columns trip, stop, sequence, departure, arrival, boardable and
        alightable, in file order, plus the stop ids the stop numbers name.
    """
    stop_index: dict[str, int] = {}
    seconds: dict[str, int] = {}
    pieces: dict[str, list[np.ndarray]] = {
        name: []
        for name in (
            "trip",
            "stop",
            "sequence",
            "departure",
            "arrival",
            "boardable",
            "alightable",
        )
    }

    # Repeated text is read as categories, so each value is parsed once
    reader = pandas.read_csv(
        GTFS_DIR / "stop_times.txt",
        usecols=STOP_TIME_COLUMNS,
        dtype={
            "trip_id": "category",
            "arrival_time": "category",
            "departure_time": "category",
            "stop_id": "category",
            "stop_sequence": "int16",
            "pickup_type": "category",
            "drop_off_type": "category",
        },
        keep_default_na=False,
        encoding="utf-8-sig",
        chunksize=READ_ROWS,
    )
    for rows in reader:
        # Each category's number, or -1 for a trip not kept
        trips = rows["trip_id"].cat
        trip_numbers = np.array(
            [trip_index.get(trip_id, -1) for trip_id in trips.categories], dtype=np.int32
        )
        trip = trip_numbers[trips.codes.to_numpy()]
        keep = trip >= 0

        stop_column = rows["stop_id"].cat
        stop_numbers = np.array(
            [stop_index.setdefault(stop, len(stop_index)) for stop in stop_column.categories],
            dtype=np.int16,
        )

        pieces["trip"].append(trip[keep])
        pieces["stop"].append(stop_numbers[stop_column.codes.to_numpy()][keep])
        pieces["sequence"].append(rows["stop_sequence"].to_numpy()[keep])

        for name, column in (("departure", "departure_time"), ("arrival", "arrival_time")):
            times = rows[column].cat
            clock = np.array(
                [seconds.setdefault(text, parse_gtfs_time(text)) for text in times.categories],
                dtype=np.int32,
            )
            pieces[name].append(clock[times.codes.to_numpy()][keep])

        # Type 1 means no pickup or no drop off
        for name, column in (("boardable", "pickup_type"), ("alightable", "drop_off_type")):
            flags = rows[column].cat
            allowed = np.array([text != "1" for text in flags.categories], dtype=bool)
            pieces[name].append(allowed[flags.codes.to_numpy()][keep])

    # Joined one column at a time, so the pieces don't double up
    columns = {}
    for name in list(pieces):
        columns[name] = np.concatenate(pieces.pop(name))
    columns["stop_ids"] = np.array(list(stop_index), dtype=str)
    return columns


def build_day(
    stop_times: dict[str, np.ndarray],
    active: np.ndarray,
    trips: list[tuple[str, str, str]],
) -> dict[str, np.ndarray]:
    """Builds one pattern's columns from the read stop_times.

    Args:
        stop_times: Columns from read_stop_times.
        active: Per trip number, whether it runs in this pattern.
        trips: Per trip number, (trip_id, route_id, headsign).

    Returns:
        The arrays a day file holds.
    """
    keep = active[stop_times["trip"]]
    trip = stop_times["trip"][keep]
    stop = stop_times["stop"][keep]
    sequence = stop_times["sequence"][keep]
    departure = stop_times["departure"][keep]
    arrival = stop_times["arrival"][keep]
    boardable = stop_times["boardable"][keep]
    alightable = stop_times["alightable"][keep]

    # Trips numbered in the order the file first lists them
    numbers, first_rows = np.unique(trip, return_index=True)
    listed = numbers[np.argsort(first_rows, kind="stable")]
    local = np.zeros(len(trips), dtype=np.int32)
    local[listed] = np.arange(len(listed), dtype=np.int32)
    trip = local[trip]

    # Each trip's stops in riding order
    riding = np.lexsort((sequence, trip))
    trip = trip[riding]
    stop = stop[riding]
    departure = departure[riding]
    arrival = arrival[riding]
    boardable = boardable[riding]
    alightable = alightable[riding]

    # One connection per consecutive pair on the same trip
    pair = np.flatnonzero(trip[:-1] == trip[1:])
    built = {
        "departures": departure[pair],
        "from_stops": stop[pair],
        "arrivals": arrival[pair + 1],
        "to_stops": stop[pair + 1],
        "trip_of": trip[pair],
        "boardable": boardable[pair],
        "alightable": alightable[pair + 1],
    }

    # Sorted by departure; ties keep riding order
    by_departure = np.argsort(built["departures"], kind="stable")
    columns = {name: values[by_departure] for name, values in built.items()}

    # Where each trip's connections landed, in riding order
    count = len(by_departure)
    trip_order = np.empty(count, dtype=np.int32)
    trip_order[by_departure] = np.arange(count, dtype=np.int32)
    trip_starts = np.searchsorted(built["trip_of"], np.arange(len(listed) + 1)).astype(np.int32)

    # Reversed time: last first, then sorted by the negated arrival
    latest_first = np.arange(count - 1, -1, -1, dtype=np.int32)
    backward = latest_first[
        np.argsort(-columns["arrivals"][latest_first], kind="stable")
    ].astype(np.int32)

    # Only the stops this pattern uses, numbered small
    used = np.unique(np.concatenate([columns["from_stops"], columns["to_stops"]]))
    small = np.int16 if len(used) < 2**15 else np.int32
    renumber = np.zeros(len(stop_times["stop_ids"]), dtype=small)
    renumber[used] = np.arange(len(used), dtype=small)
    columns["from_stops"] = renumber[columns["from_stops"]]
    columns["to_stops"] = renumber[columns["to_stops"]]

    columns["departures"] = columns["departures"].astype(np.int32)
    columns["arrivals"] = columns["arrivals"].astype(np.int32)
    columns["trip_of"] = columns["trip_of"].astype(np.int16 if len(listed) < 2**15 else np.int32)
    columns["backward_order"] = backward
    columns["trip_order"] = trip_order
    columns["trip_starts"] = trip_starts
    columns["stops"] = pack(stop_times["stop_ids"][used].tolist())
    columns["trip_ids"] = pack([trips[number][0] for number in listed])
    columns["routes"] = pack([trips[number][1] for number in listed])
    columns["headsigns"] = pack([trips[number][2] for number in listed])
    return columns


def write_day(path: Path, columns: dict[str, np.ndarray], scraped_at: float) -> None:
    """Writes one day file in full before it replaces the old one.

    Args:
        path: Where it goes.
        columns: The day's arrays.
        scraped_at: When the tables it came from were scraped.
    """
    DAYS_DIR.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(".part")
    with partial.open("wb") as day_file:
        np.savez(day_file, stamp=np.array(scraped_at), **columns)
    os.replace(partial, path)


def build(patterns: list[frozenset], scraped_at: float) -> None:
    """Reads stop_times once and writes a file for each pattern.

    Args:
        patterns: The service id sets to build.
        scraped_at: When the tables were scraped.
    """
    wanted = set().union(*patterns) if patterns else set()

    # Every trip a wanted service runs
    numbered = {service: number for number, service in enumerate(sorted(wanted))}
    trips = []
    services_of = []
    with (GTFS_DIR / "trips.txt").open(encoding="utf-8-sig", newline="") as table_file:
        for row in csv.DictReader(table_file):
            service = numbered.get(row["service_id"])
            if service is not None:
                route = sys.intern(row["route_id"])
                trips.append((row["trip_id"], route, sys.intern(row["trip_headsign"])))
                services_of.append(service)
    trip_index = {trip_id: number for number, (trip_id, _, _) in enumerate(trips)}

    stop_times = read_stop_times(trip_index)
    services_of = np.array(services_of, dtype=np.int32)
    for services in patterns:
        active = np.isin(services_of, [numbered[service] for service in services])
        write_day(day_path(services), build_day(stop_times, active, trips), scraped_at)


@lru_cache(maxsize=16)
def services_on(target: date, scraped_at: float) -> frozenset:
    """Reads the services running on a date.

    Args:
        target: The service date.
        scraped_at: When the tables were scraped.

    Returns:
        The active service ids.
    """
    return frozenset(active_service_ids(target))


def read_day(path: Path, scraped_at: float) -> Day | None:
    """Reads a day file made from the current tables.

    Args:
        path: The file.
        scraped_at: When the tables were scraped.

    Returns:
        The day, or None when it is missing or from older tables.
    """
    try:
        with np.load(path) as stored:
            if float(stored["stamp"]) != scraped_at:
                return None
            return Day({name: stored[name] for name in stored.files})
    except FileNotFoundError:
        return None


def empty_day() -> Day:
    """Builds a day with nothing running.

    Returns:
        A day with no connections.
    """
    numbers = np.zeros(0, dtype=np.int32)
    flags = np.zeros(0, dtype=bool)
    words = np.zeros(0, dtype=np.uint8)
    return Day(
        {
            "departures": numbers,
            "arrivals": numbers,
            "from_stops": numbers,
            "to_stops": numbers,
            "trip_of": numbers,
            "boardable": flags,
            "alightable": flags,
            "backward_order": numbers,
            "trip_order": numbers,
            "trip_starts": np.zeros(1, dtype=np.int32),
            "stops": words,
            "trip_ids": words,
            "routes": words,
            "headsigns": words,
        }
    )


@lru_cache(maxsize=CACHED_DAYS)
def load_pattern(services: frozenset, scraped_at: float) -> Day:
    """Loads one schedule pattern, building its file when it is missing.

    Args:
        services: The service ids running.
        scraped_at: When the tables were scraped.

    Returns:
        The pattern's day.
    """
    if not services:
        return empty_day()

    path = day_path(services)
    day = read_day(path, scraped_at)
    if day is not None:
        return day

    # Another thread may be writing it already
    with _building:
        day = read_day(path, scraped_at)
        if day is None:
            build([services], scraped_at)
            day = read_day(path, scraped_at)
    return day


def load_service_day(target: date, scraped_at: float) -> Day:
    """Loads the connections running on a date.

    Args:
        target: The service date.
        scraped_at: When the tables were scraped.

    Returns:
        The date's day, shared with every date on the same pattern.
    """
    return load_pattern(services_on(target, scraped_at), scraped_at)


def build_all() -> int:
    """Writes a file for every pattern from yesterday to the timetable's end.

    Returns:
        How many patterns were written.
    """
    stamp = gtfs_stamp()
    first = service_date_at(now_in_boston()) - timedelta(days=1)
    last = last_service_date(stamp) or first

    patterns = set()
    day = first
    while day <= last:
        services = services_on(day, stamp)
        if services:
            patterns.add(services)
        day += timedelta(days=1)

    with _building:
        build(sorted(patterns, key=sorted), stamp)

        # Files for patterns no longer running
        kept = {day_path(services).name for services in patterns}
        for stale in DAYS_DIR.glob("*.npz"):
            if stale.name not in kept:
                stale.unlink()

    return len(patterns)


def days_missing() -> bool:
    """Checks whether today's or tomorrow's file is missing or old.

    Returns:
        Whether the files need building.
    """
    stamp = gtfs_stamp()
    today = service_date_at(now_in_boston())
    for target in (today, today + timedelta(days=1)):
        services = services_on(target, stamp)
        if services and read_day(day_path(services), stamp) is None:
            return True
    return False


def forget() -> None:
    """Lets go of every cached table, so a new timetable loads in their place."""
    load_pattern.cache_clear()
    services_on.cache_clear()
    load_stops.cache_clear()
    load_routes.cache_clear()
    load_footpaths.cache_clear()
    last_service_date.cache_clear()


def warm() -> None:
    """Loads every cached table, writing the ready-made days first if they're missing."""
    if days_missing():
        print(f"timetable: {build_all()} ready-made days written")

    stamp = gtfs_stamp()
    load_stops(stamp)
    load_routes(stamp)
    load_footpaths(stamp)
    load_service_day(service_date_at(now_in_boston()), stamp)


if __name__ == "__main__":
    print(f"Writing ready-made days -> {DAYS_DIR}")
    print(f"{build_all()} patterns written")
