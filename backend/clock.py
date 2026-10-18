"""Read the time in Boston."""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

# The zone every timetable and arrival is in
ZONE = ZoneInfo("America/New_York")


def now_in_boston() -> datetime:
    """Reads the time in Boston.

    Returns:
        The current moment in Boston.
    """
    return datetime.now(ZONE)


def in_boston(moment: datetime) -> datetime:
    """Moves a moment onto Boston's clock.

    Args:
        moment: Any moment.

    Returns:
        The same moment, read in Boston.
    """
    if moment.tzinfo is None:
        return moment.replace(tzinfo=ZONE)
    return moment.astimezone(ZONE)


def moment_at(service_date: date, seconds: int) -> datetime:
    """Turns seconds into a service day into the moment they name.

    Args:
        service_date: The service day's date.
        seconds: Seconds after that day's midnight.

    Returns:
        The moment.
    """
    wall = datetime.combine(service_date, time()) + timedelta(seconds=seconds)
    return wall.replace(tzinfo=ZONE)
