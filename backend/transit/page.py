"""Gather what the transit page draws."""

from datetime import datetime, time
from typing import TypedDict

from backend.lateness import (
    LATE_SECONDS,
    ROLLING_SECONDS,
    Reading,
    TypicalReading,
    bucket_of,
    read_series,
    read_resumes,
    read_typical,
    read_headways,
)
from backend.lines import BRANCH_LIST, LINES
from backend.status import SystemStatus
from backend.timetable import (
    SERVICE_ROLLOVER_HOUR,
    gtfs_stamp,
    service_date_at,
    service_seconds,
)


class Transit(TypedDict):
    """Every line's state, and how each has run since the day began."""

    status: SystemStatus
    series: dict[str, list[Reading]]
    typical: dict[str, list[TypicalReading]]
    headways: dict[str, int]
    resumes: dict[str, str]
    branches: dict[str, list[dict[str, str]]]
    late_minutes: int
    rolling_minutes: int


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
    return {
        "status": status,
        "series": read_series(began, bucket_of(now)),
        "typical": read_typical(began, bucket_of(now)),
        "headways": read_headways(
            service_date_at(now), service_seconds(now) // 3600, gtfs_stamp()
        ),
        "resumes": read_resumes(bucket_of(now), gtfs_stamp()),
        "branches": BRANCH_LIST,
        "late_minutes": LATE_SECONDS // 60,
        "rolling_minutes": ROLLING_SECONDS // 60,
    }
