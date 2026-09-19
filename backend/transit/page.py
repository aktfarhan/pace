"""Gather what the transit page draws."""

from datetime import datetime, time
from typing import TypedDict

from backend.lateness import (
    LATE_SECONDS,
    ROLLING_SECONDS,
    Reading,
    bucket_of,
    read_series,
    read_resumes,
    read_typical,
    read_headways,
)
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
    typical: dict[str, list[Reading]]
    headways: dict[str, int]
    resumes: dict[str, str]
    late_minutes: int
    rolling_minutes: int


def read_transit(status: SystemStatus, now: datetime) -> Transit:
    """Puts the day's readings beside the line's own cards.

    Args:
        status: A reading of the alert feed.
        now: The local time.

    Returns:
        The cards and the readings.
    """
    began = datetime.combine(
        service_date_at(now), time(SERVICE_ROLLOVER_HOUR), now.tzinfo
    )
    return {
        "status": status,
        "series": read_series(began, bucket_of(now)),
        "typical": read_typical(began, bucket_of(now)),
        "headways": read_headways(
            service_date_at(now), service_seconds(now) // 3600, gtfs_stamp()
        ),
        "resumes": read_resumes(bucket_of(now), gtfs_stamp()),
        "late_minutes": LATE_SECONDS // 60,
        "rolling_minutes": ROLLING_SECONDS // 60,
    }
