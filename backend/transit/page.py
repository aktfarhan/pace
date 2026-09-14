"""Gather what the transit page draws."""

from datetime import datetime, time
from typing import TypedDict

from backend.lateness import Reading, bucket_of, read_series, read_typical
from backend.status import SystemStatus
from backend.timetable import SERVICE_ROLLOVER_HOUR, service_date_at


class Transit(TypedDict):
    """Every line's state, and how each has run since the day began."""

    status: SystemStatus
    series: dict[str, list[Reading]]
    typical: dict[str, list[Reading]]


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
        "series": read_series(began, now),
        "typical": read_typical(began, bucket_of(now)),
    }
