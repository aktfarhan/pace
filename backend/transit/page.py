"""Gather what the transit page draws."""

import hashlib
import json
from datetime import datetime, time
from functools import lru_cache
from typing import TypedDict

from backend.reliability.lateness import (
    LATE_SECONDS,
    ROLLING_SECONDS,
    Reading,
    TypicalReading,
    bucket_of,
    read_series,
    readings_saved,
    read_resumes,
    read_typical,
    read_headways,
)
from backend.mbta.lines import BRANCH_LIST, LINES
from backend.mbta.status import SystemStatus
from backend.planner.timetable import (
    SERVICE_ROLLOVER_HOUR,
    gtfs_stamp,
    service_date_at,
    service_seconds,
)


class Transit(TypedDict):
    """Every line's state, and which readings go with it."""

    status: SystemStatus
    readings: str
    headways: dict[str, int]
    resumes: dict[str, str]
    timetable: bool
    branches: dict[str, list[dict[str, str]]]
    late_minutes: int
    rolling_minutes: int


class Readings(TypedDict):
    """How each line has run since the day began, and how it usually runs."""

    series: dict[str, list[Reading]]
    typical: dict[str, list[TypicalReading]]


@lru_cache(maxsize=2)
def readings_during(began: datetime, edge: datetime, saved: int) -> tuple[bytes, str]:
    """Builds the readings once per quarter hour and per save.

    Args:
        began: When the service day started.
        edge: The quarter hour the readings run up to.
        saved: How many times the readings have gained a quarter.

    Returns:
        Tuple of (the readings as JSON, a short name that changes with them).
    """
    readings: Readings = {
        "series": read_series(began, edge),
        "typical": read_typical(began, edge),
    }
    body = json.dumps(readings, separators=(",", ":")).encode()
    return body, hashlib.blake2b(body, digest_size=8).hexdigest()


def read_readings(now: datetime) -> bytes:
    """Reads the day's readings as JSON.

    Args:
        now: The time.

    Returns:
        The readings, the same bytes for everyone in the quarter hour.
    """
    return readings_during(began_of(now), bucket_of(now), readings_saved())[0]


def began_of(now: datetime) -> datetime:
    """Finds when the service day holding began.

    Args:
        now: The time.

    Returns:
        The service day's rollover hour.
    """
    return datetime.combine(
        service_date_at(now), time(SERVICE_ROLLOVER_HOUR), now.tzinfo
    )


def read_usual(now: datetime) -> dict[str, int]:
    """Reads the share each line typically runs late at this time of day.

    Args:
        now: The time.

    Returns:
        The latest typical share per line.
    """
    typical = read_typical(began_of(now), bucket_of(now))
    usual: dict[str, int] = {}
    for line_id, _, _, _ in LINES:
        if typical[line_id]:
            usual[line_id] = typical[line_id][-1]["share"]
    return usual


def read_transit(status: SystemStatus, now: datetime) -> Transit:
    """Puts the day's readings beside the line's own cards.

    Args:
        status: A reading of the alert feed.
        now: The local time.

    Returns:
        The cards and the readings.
    """
    began = began_of(now)

    # A timetable that can't be read should not look like a quiet night
    try:
        stamp = gtfs_stamp()
        headways = read_headways(
            service_date_at(now), service_seconds(now) // 3600, stamp
        )
        resumes = read_resumes(bucket_of(now), stamp)
        timetable = True
    except (OSError, KeyError, ValueError) as error:
        print(f"transit: timetable unreadable: {error}")
        headways = {}
        resumes = {}
        timetable = False

    # The page fetches the readings only when this changes
    _, readings = readings_during(began, bucket_of(now), readings_saved())

    return {
        "status": status,
        "readings": readings,
        "headways": headways,
        "resumes": resumes,
        "timetable": timetable,
        "branches": BRANCH_LIST,
        "late_minutes": LATE_SECONDS // 60,
        "rolling_minutes": ROLLING_SECONDS // 60,
    }
