"""The HTTP server: streaming endpoint that answers a query."""

import asyncio
import json
import time
from collections.abc import AsyncGenerator, Iterator
from contextlib import asynccontextmanager
from datetime import timedelta, timezone
from functools import lru_cache

import psycopg
from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from backend.ask import ask_stream
from backend.board import Planned, plan_saved
from backend.clock import now_in_boston
from backend.lateness import poll, read_resting, resume, save_open
from backend.places import Saved, SavedPlace, add_place, read_places, remove_place
from backend.trips import Kept, SavedTrip, add_trip, read_trips, remove_trip
from backend.risk import warm as warm_model
from backend.status import SystemStatus, read_status, without_alerts
from backend.timetable import (
    active_service_ids,
    gtfs_stamp,
    last_service_date,
    service_date_at,
    warm,
)
from backend.transit.page import Transit, read_transit, read_usual
from data.mbta.scrape_gtfs import refresh
from data.schema import connect

# Where the frontend runs
ORIGINS = ["http://localhost:3000"]

# The longest askable question
MAX_QUERY = 500

# The longest a saved place's fields may be
MAX_LABEL = 60
MAX_ADDRESS = 200

# The longest a saved trip's ends may be
MAX_END = 120

# Seconds before the alert feed is read again
STATUS_TTL = 20.0

# Proxies buffer a stream unless told not to
STREAM_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}

CHUNK_COUNT = "SELECT count(*) FROM chunks;"

# When the timetable is fetched again each night
REFRESH_HOUR = 3
REFRESH_MINUTE = 30

# A timetable ending sooner than this many days gets a warning
TIMETABLE_WARN_DAYS = 7


def seconds_until_refresh() -> float:
    """Counts down to the next nightly timetable refresh.

    Returns:
        Seconds until the next 3:30 AM in Boston.
    """
    now = now_in_boston()
    due = now.replace(hour=REFRESH_HOUR, minute=REFRESH_MINUTE, second=0, microsecond=0)
    if due <= now:
        due += timedelta(days=1)
    return (due.astimezone(timezone.utc) - now.astimezone(timezone.utc)).total_seconds()


async def refresh_nightly() -> None:
    """Fetches the timetable again each night."""
    while True:
        await asyncio.sleep(seconds_until_refresh())

        # A failed night keeps yesterday's timetable
        try:
            if await asyncio.to_thread(refresh):
                await asyncio.to_thread(warm)
                print("timetable: refreshed")
            else:
                print("timetable: already current")
        except Exception as error:
            print(f"timetable: refresh failed: {type(error).__name__}: {error}")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Reads the timetable and starts watching the lines.

    Args:
        app: The server.

    Yields:
        Once, with the tables loaded and the poller running.
    """
    warm()
    warm_model()

    # The quarter hour saved when the server last stopped
    await asyncio.to_thread(resume, now_in_boston())

    watcher = asyncio.create_task(poll())
    refresher = asyncio.create_task(refresh_nightly())
    try:
        yield
    finally:
        watcher.cancel()
        refresher.cancel()

        # The open quarter hour
        await asyncio.to_thread(save_open)


# The server
app = FastAPI(
    title="Pace",
    lifespan=lifespan,
    docs_url="/v1/docs",
    openapi_url="/v1/openapi.json",
    redoc_url=None,
    swagger_ui_oauth2_redirect_url=None,
)

# The day's readings squash to a tenth
app.add_middleware(GZipMiddleware, minimum_size=1024, compresslevel=6)

# A browser blocks a call to another port unless the server allows it
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "X-Pace-Code"],
)


class Question(BaseModel):
    """One question posted to /v1/ask."""

    model_config = ConfigDict(str_strip_whitespace=True)

    query: str = Field(min_length=1, max_length=MAX_QUERY)


class NewPlace(BaseModel):
    """One place posted to /v1/places."""

    model_config = ConfigDict(str_strip_whitespace=True)

    label: str = Field(min_length=1, max_length=MAX_LABEL)
    address: str = Field(min_length=1, max_length=MAX_ADDRESS)


class NewTrip(BaseModel):
    """One trip posted to /v1/trips."""

    model_config = ConfigDict(str_strip_whitespace=True)

    origin: str = Field(min_length=1, max_length=MAX_END)
    destination: str = Field(min_length=1, max_length=MAX_END)


def event(name: str, data: dict) -> str:
    """Formats one server-sent event.

    Args:
        name: The event name.
        data: The event payload.

    Returns:
        An event and data line.
    """
    return f"event: {name}\ndata: {json.dumps(data)}\n\n"


def stream(query: str) -> Iterator[str]:
    """Runs the pipeline and formats every step as an event.

    Args:
        query: The user's question.

    Yields:
        One event per stage, then the answer.
    """
    try:
        for name, data in ask_stream(query):
            yield event(name, data)
    except Exception as error:
        yield event("error", {"message": str(error)})


@app.post("/v1/ask")
def answer_query(question: Question) -> StreamingResponse:
    """Answers one question as a stream of stage events.

    Args:
        question: The posted query.

    Returns:
        A text/event-stream response.
    """
    return StreamingResponse(
        stream(question.query),
        media_type="text/event-stream",
        headers=STREAM_HEADERS,
    )


@lru_cache(maxsize=1)
def status_during(bucket: int) -> SystemStatus:
    """Reads the alert feed once per bucket of time.

    Args:
        bucket: The STATUS_TTL-wide window.

    Returns:
        That window's reading. Only the current bucket is kept.
    """
    now = now_in_boston()

    # Without a timetable the cards fall back to alerts
    try:
        resting = read_resting(now)
    except (OSError, KeyError, ValueError) as error:
        print(f"status: timetable unreadable: {error}")
        resting = {}

    return read_status(read_usual(now), resting)


@app.get("/v1/status")
def check_status(alerts: bool = False) -> SystemStatus:
    """Reports every rail line's state.

    Args:
        alerts: Whether each line carries its own alerts.

    Returns:
        One card per line.
    """
    live = status_during(int(time.monotonic() // STATUS_TTL))
    if alerts:
        return live
    return without_alerts(live)


@app.get("/v1/transit")
def check_transit() -> Transit:
    """Reports every line's state and how it has run since the day began.

    Returns:
        Each line's card with their alerts, and the day's readings.
    """
    live = status_during(int(time.monotonic() // STATUS_TTL))
    return read_transit(live, now_in_boston())


@app.get("/v1/places")
def list_places(x_pace_code: str | None = Header(default=None)) -> list[SavedPlace]:
    """Reads the places saved against the user's code.

    Args:
        x_pace_code: The user's code.

    Returns:
        The saved places, oldest first.
    """
    return read_places(x_pace_code)


@app.post("/v1/places")
def save_place(
    place: NewPlace, x_pace_code: str | None = Header(default=None)
) -> Saved:
    """Saves one place, giving a code to a user without one.

    Args:
        place: The posted label and address.
        x_pace_code: The user's code.

    Returns:
        The stored place and the code it belongs to.
    """
    return add_place(x_pace_code, place.label, place.address)


@app.delete("/v1/places/{place_id}", status_code=204)
def drop_place(place_id: int, x_pace_code: str | None = Header(default=None)) -> None:
    """Removes one of the user's saved places.

    Args:
        place_id: The place to remove.
        x_pace_code: The user's code.
    """
    remove_place(x_pace_code, place_id)


@app.get("/v1/trips")
def list_trips(x_pace_code: str | None = Header(default=None)) -> list[SavedTrip]:
    """Reads the trips saved against the user's code.

    Args:
        x_pace_code: The user's code.

    Returns:
        The saved trips, oldest first.
    """
    return read_trips(x_pace_code)


@app.post("/v1/trips")
def save_trip(trip: NewTrip, x_pace_code: str | None = Header(default=None)) -> Kept:
    """Saves one trip, giving a code to a user without one.

    Args:
        trip: The posted origin and destination.
        x_pace_code: The user's code.

    Returns:
        The stored trip and the code it belongs to.
    """
    return add_trip(x_pace_code, trip.origin, trip.destination)


@app.delete("/v1/trips/{trip_id}", status_code=204)
def drop_trip(trip_id: int, x_pace_code: str | None = Header(default=None)) -> None:
    """Removes one of the user's saved trips.

    Args:
        trip_id: The trip to remove.
        x_pace_code: The user's code.
    """
    remove_trip(x_pace_code, trip_id)


@app.get("/v1/board")
def list_board(x_pace_code: str | None = Header(default=None)) -> list[Planned]:
    """Plans every trip saved against the user's code.

    Args:
        x_pace_code: The user's code.

    Returns:
        One entry per saved trip, oldest first.
    """
    return plan_saved(x_pace_code)


def timetable_health() -> dict:
    """Reports whether the timetable covers today and tomorrow, and when it ends.

    Returns:
        Whether it is fine, the dates it covers, and a warning when it isn't.
    """
    today = service_date_at(now_in_boston())
    tomorrow = today + timedelta(days=1)
    try:
        ends = last_service_date(gtfs_stamp())
        covers_today = bool(active_service_ids(today))
        covers_tomorrow = bool(active_service_ids(tomorrow))
    except (OSError, KeyError, ValueError) as error:
        return {"ok": False, "warning": f"The timetable can't be read: {error}"}

    warning = None
    if not covers_today or not covers_tomorrow:
        warning = "The timetable has no service for today or tomorrow"
    elif ends is None or (ends - today).days < TIMETABLE_WARN_DAYS:
        warning = f"The timetable ends on {ends}; the nightly refresh may be failing"

    return {
        "ok": warning is None,
        "today": covers_today,
        "tomorrow": covers_tomorrow,
        "ends": ends.isoformat() if ends else None,
        "warning": warning,
    }


@app.get("/v1/health")
def check_health() -> dict:
    """Reports whether the database is reachable and the timetable is current.

    Returns:
        The chunk count and the timetable's state, or what went wrong.
    """
    timetable = timetable_health()
    try:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(CHUNK_COUNT)
            chunks = cursor.fetchone()[0]
    except psycopg.Error as error:
        return {"ok": False, "error": str(error), "timetable": timetable}
    return {"ok": timetable["ok"], "chunks": chunks, "timetable": timetable}
