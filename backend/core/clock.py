"""Read the time in Boston."""

import re
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

# The zone every timetable and arrival is in
ZONE = ZoneInfo("America/New_York")

# A clock time as people and the model write it
CLOCK = re.compile(r"^(\d{1,2})(?::(\d{2}))?\s*([ap])\.?\s*m?\.?$|^(\d{1,2}):(\d{2})$")

# Clock words
CLOCK_WORDS = {"noon": 12 * 3600, "midnight": 0}


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


def parse_clock(text: str | None) -> int | None:
    """Turns a written clock time into seconds since midnight.

    Args:
        text: A clock time.

    Returns:
        Seconds since midnight, or None.
    """
    if not text:
        return None
    text = text.strip().lower()
    if text in CLOCK_WORDS:
        return CLOCK_WORDS[text]

    match = CLOCK.match(text)
    if match is None:
        return None

    # 12-hour times
    if match.group(1):
        hour, minute = int(match.group(1)), int(match.group(2) or 0)
        if not 1 <= hour <= 12 or minute > 59:
            return None
        hour = hour % 12 + (12 if match.group(3) == "p" else 0)
        return hour * 3600 + minute * 60

    # 24-hour times
    hour, minute = int(match.group(4)), int(match.group(5))
    if hour > 23 or minute > 59:
        return None
    return hour * 3600 + minute * 60
