"""Caps how often visitors can ask and save."""

import os
import threading
import time
from collections.abc import Callable, Hashable

from dotenv import load_dotenv
from fastapi import HTTPException, Request

from backend.core.clock import now_in_boston

# Reads the .env
load_dotenv()

# Render's edge sets this to the visitor's address
VISITOR_HEADER = "true-client-ip"

# Questions the whole site answers in a day
DAILY_QUESTIONS = int(os.environ.get("DAILY_QUESTIONS", "200"))

# Each visitor's questions per minute and per day
ASK_PER_MINUTE = 5
ASK_PER_DAY = 10

# Each visitor's saves and removals per minute
SAVE_PER_MINUTE = 20

# What a refused visitor reads
RUSHED = "That's a lot of questions at once. Try again in a minute."
TIRED = "You've asked a lot of questions today. Try again tomorrow."
SPENT = "Pace has answered all the questions it can today. Try again tomorrow."
HURRIED = "Too many changes at once. Try again in a minute."

# The one key the site-wide count is kept under
SITE = "site"


def this_minute() -> int:
    """Names the current minute.

    Returns:
        Whole minutes on the server's clock.
    """
    return int(time.monotonic() // 60)


def this_day() -> Hashable:
    """Names the current day in Boston.

    Returns:
        Today's date in Boston.
    """
    return now_in_boston().date()


class Counter:
    """Counts each visitor's requests."""

    def __init__(self, most: int, window: Callable[[], Hashable]) -> None:
        """Sets the cap and how windows are named.

        Args:
            most: Requests allowed per visitor per window.
            window: Names the current window.
        """
        self.most = most
        self.window = window
        self.current: Hashable = None
        self.counts: dict[str, int] = {}
        self.lock = threading.Lock()

    def take(self, visitor: str) -> bool:
        """Counts one request if the visitor has any left.

        Args:
            visitor: Who is asking.

        Returns:
            Whether the request is allowed.
        """
        window = self.window()
        with self.lock:
            # A new window starts every count over
            if window != self.current:
                self.current = window
                self.counts.clear()

            used = self.counts.get(visitor, 0)
            if used >= self.most:
                return False
            self.counts[visitor] = used + 1
            return True


ASK_MINUTE = Counter(ASK_PER_MINUTE, this_minute)
ASK_DAY = Counter(ASK_PER_DAY, this_day)
SITE_DAY = Counter(DAILY_QUESTIONS, this_day)
SAVE_MINUTE = Counter(SAVE_PER_MINUTE, this_minute)


def visitor(request: Request) -> str:
    """Reads who sent a request.

    Args:
        request: The incoming request.

    Returns:
        The visitor's address from Render's edge.
    """
    sent = request.headers.get(VISITOR_HEADER)
    if sent:
        return sent
    return request.client.host if request.client else "unknown"


def limit_asks(request: Request) -> None:
    """Refuses a question past the visitor's or the site's cap.

    Args:
        request: The incoming request.

    Raises:
        HTTPException: 429 with the reason to show.
    """
    who = visitor(request)
    if not ASK_MINUTE.take(who):
        raise HTTPException(status_code=429, detail=RUSHED)
    if not ASK_DAY.take(who):
        raise HTTPException(status_code=429, detail=TIRED)

    # Checked last so a refused visitor doesn't use up the site's day
    if not SITE_DAY.take(SITE):
        raise HTTPException(status_code=429, detail=SPENT)


def limit_saves(request: Request) -> None:
    """Refuses a save or removal past the visitor's cap.

    Args:
        request: The incoming request.

    Raises:
        HTTPException: 429 with the reason to show.
    """
    if not SAVE_MINUTE.take(visitor(request)):
        raise HTTPException(status_code=429, detail=HURRIED)
