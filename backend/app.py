"""The HTTP server: streaming endpoint that answers a query."""

import asyncio
import gzip
import json
import os
import time
from collections.abc import AsyncGenerator, Iterator
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from functools import lru_cache

import psycopg
from anyio import to_thread
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse
from openai import OpenAIError
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from backend.assistant.ask import ask_stream
from backend.assistant.retrieve import searchable
from backend.saved.board import Planned, plan_saved
from backend.geo.geocode import Place, forget_places, suggest
from backend.core.clock import now_in_boston
from backend.reliability.lateness import (
    bucket_of,
    poll,
    read_resting,
    readings_saved,
    resume,
    save_open,
)
from backend.saved.places import (
    Saved,
    SavedPlace,
    Unfound,
    add_place,
    read_places,
    remove_place,
)
from backend.saved.trips import Kept, SavedTrip, add_trip, read_trips, remove_trip
from backend.reliability.risk import warm as warm_model
from backend.mbta.status import SystemStatus, read_status, without_alerts
from backend.planner.days import forget, warm
from backend.planner.timetable import (
    active_service_ids,
    gtfs_stamp,
    last_service_date,
    service_date_at,
)
from backend.transit.page import Transit, read_readings, read_transit, read_usual
from backend.planner.scrape_gtfs import refresh
from backend.core.db import borrow, close_pool
from backend.core.limits import limit_asks, limit_saves, limit_suggests

# Where the frontend runs
ORIGINS = [
    origin.strip()
    for origin in os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
]

# The longest askable question
MAX_QUERY = 300

# The longest a saved place's fields may be
MAX_LABEL = 60
MAX_ADDRESS = 200

# The longest a saved trip's ends may be
MAX_END = 120

# Where a picked place may be
LAT_RANGE = (41.0, 43.5)
LON_RANGE = (-74.0, -69.5)

# What a visitor reads when a saved address can't be found
NOT_FOUND = "We couldn't find that address"

# Seconds before the alert feed is read again
STATUS_TTL = 20.0

# Requests worked on at once; the rest wait their turn
MAX_THREADS = 8

# Turns the Transit page into JSON
TRANSIT_JSON = TypeAdapter(Transit)

# Proxies buffer a stream unless told not to
STREAM_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}

CHUNK_COUNT = "SELECT count(*) FROM chunks;"

# What a visitor reads when a question fails
PAUSED = "Questions are paused right now."
UNANSWERED = "Couldn't get an answer"

# When the timetable is fetched again each night
REFRESH_HOUR = 3
REFRESH_MINUTE = 30

# A timetable ending sooner than this many days gets a warning
TIMETABLE_WARN_DAYS = 7

# A timetable older than this is checked for a newer one at start-up
STALE_SECONDS = 20 * 3600


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


async def refresh_timetable() -> None:
    """Fetches the timetable and loads it if it changed."""
    forget_places()

    # A failed refresh keeps the current timetable
    try:
        if await asyncio.to_thread(refresh):
            # The old timetable goes before the new one loads
            forget()
            await asyncio.to_thread(warm)
            print("timetable: refreshed")
        else:
            print("timetable: already current")
    except Exception as error:
        print(f"timetable: refresh failed: {type(error).__name__}: {error}")


async def refresh_nightly() -> None:
    """Fetches the timetable at start-up if it's old, then again each night."""
    if time.time() - gtfs_stamp() > STALE_SECONDS:
        await refresh_timetable()

    while True:
        await asyncio.sleep(seconds_until_refresh())
        await refresh_timetable()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Reads the timetable and starts watching the lines.

    Args:
        app: The server.

    Yields:
        Once, with the tables loaded and the poller running.
    """
    to_thread.current_default_thread_limiter().total_tokens = MAX_THREADS
    warm()
    warm_model()

    # The question search, unless the database is not up yet
    try:
        await asyncio.to_thread(searchable)
    except psycopg.Error as error:
        print(f"search: not loaded yet: {type(error).__name__}: {error}")

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
        await asyncio.to_thread(close_pool)


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
    lat: float | None = Field(default=None, ge=LAT_RANGE[0], le=LAT_RANGE[1])
    lon: float | None = Field(default=None, ge=LON_RANGE[0], le=LON_RANGE[1])


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


def stream(query: str, code: str | None) -> Iterator[str]:
    """Runs the pipeline and formats every step as an event.

    Args:
        query: The user's question.
        code: The user's code.

    Yields:
        One event per stage, then the answer.
    """
    try:
        for name, data in ask_stream(query, code):
            yield event(name, data)
    except OpenAIError as error:
        print(f"ask: OpenAI failed: {type(error).__name__}: {error}")
        yield event("error", {"message": PAUSED})
    except Exception as error:
        print(f"ask: failed: {type(error).__name__}: {error}")
        yield event("error", {"message": UNANSWERED})


@app.post("/v1/ask")
def answer_query(
    question: Question,
    request: Request,
    x_pace_code: str | None = Header(default=None),
) -> StreamingResponse:
    """Answers one question as a stream of stage events.

    Args:
        question: The posted query.
        request: Who sent it.
        x_pace_code: The user's code.

    Returns:
        A text/event-stream response.
    """
    limit_asks(request)

    return StreamingResponse(
        stream(question.query, x_pace_code),
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


@lru_cache(maxsize=1)
def transit_during(bucket: int, quarter: datetime, saved: int) -> tuple[bytes, bytes]:
    """Builds the Transit page once per status window.

    Args:
        bucket: The STATUS_TTL-wide window.
        quarter: The quarter hour the readings run up to.
        saved: How many times the readings have gained a quarter.

    Returns:
        Tuple of (the page as JSON, the same compressed).
    """
    page = read_transit(status_during(bucket), now_in_boston())
    body = TRANSIT_JSON.dump_json(TRANSIT_JSON.validate_python(page))
    return body, gzip.compress(body, compresslevel=6, mtime=0)


@app.get("/v1/transit", response_model=Transit)
def check_transit(accept_encoding: str = Header(default="")) -> Response:
    """Reports every line's state and how it has run since the day began.

    Args:
        accept_encoding: What the browser can decompress.

    Returns:
        Each line's card with their alerts, and the day's readings.
    """
    now = now_in_boston()
    body, squashed = transit_during(
        int(time.monotonic() // STATUS_TTL), bucket_of(now), readings_saved()
    )

    # Same bytes for every visitor in the window
    if "gzip" in accept_encoding:
        return Response(
            squashed,
            media_type="application/json",
            headers={"Content-Encoding": "gzip", "Vary": "Accept-Encoding"},
        )
    return Response(body, media_type="application/json")


@app.get("/v1/readings")
def check_readings() -> Response:
    """Reports how each line has run since the day began, and how it usually runs.

    Returns:
        The day's readings, which change once a quarter hour.
    """
    return Response(read_readings(now_in_boston()), media_type="application/json")


@app.get("/v1/places")
def list_places(x_pace_code: str | None = Header(default=None)) -> list[SavedPlace]:
    """Reads the places saved against the user's code.

    Args:
        x_pace_code: The user's code.

    Returns:
        The saved places, oldest first.
    """
    return read_places(x_pace_code)


@app.post("/v1/places", dependencies=[Depends(limit_saves)])
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
    # Both halves of a picked spot, or neither
    spot = None
    if place.lat is not None and place.lon is not None:
        spot = (place.lat, place.lon)

    try:
        return add_place(x_pace_code, place.label, place.address, spot)
    except Unfound:
        raise HTTPException(status_code=422, detail=NOT_FOUND) from None


@app.get("/v1/places/suggest", dependencies=[Depends(limit_suggests)])
def suggest_places(q: str = Query(min_length=1, max_length=MAX_ADDRESS)) -> list[Place]:
    """Suggests the places a half-typed address or name could be.

    Args:
        q: What the user has typed so far.

    Returns:
        Up to five places, best first.
    """
    with borrow() as connection, connection.cursor() as cursor:
        return suggest(cursor, q)


@app.delete(
    "/v1/places/{place_id}", status_code=204, dependencies=[Depends(limit_saves)]
)
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


@app.post("/v1/trips", dependencies=[Depends(limit_saves)])
def save_trip(trip: NewTrip, x_pace_code: str | None = Header(default=None)) -> Kept:
    """Saves one trip, giving a code to a user without one.

    Args:
        trip: The posted origin and destination.
        x_pace_code: The user's code.

    Returns:
        The stored trip and the code it belongs to.
    """
    return add_trip(x_pace_code, trip.origin, trip.destination)


@app.delete(
    "/v1/trips/{trip_id}", status_code=204, dependencies=[Depends(limit_saves)]
)
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
        print(f"health: timetable unreadable: {type(error).__name__}: {error}")
        return {"ok": False, "warning": "The timetable can't be read"}

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


@app.api_route("/v1/ping", methods=["GET", "HEAD"])
async def check_ping() -> dict:
    """Answers to keep the server awake.

    Returns:
        Always ok.
    """
    return {"ok": True}


@app.api_route("/v1/health", methods=["GET", "HEAD"])
def check_health() -> JSONResponse:
    """Reports whether the database is reachable and the timetable is current.

    Returns:
        The chunk count and the timetable's state, with 503 when something is wrong.
    """
    timetable = timetable_health()
    try:
        with borrow() as connection, connection.cursor() as cursor:
            cursor.execute(CHUNK_COUNT)
            chunks = cursor.fetchone()[0]
    except psycopg.Error as error:
        print(f"health: database unreachable: {type(error).__name__}: {error}")
        report = {
            "ok": False,
            "error": "The database can't be reached",
            "timetable": timetable,
        }
    else:
        report = {"ok": timetable["ok"], "chunks": chunks, "timetable": timetable}

    # A monitor reads the status code
    return JSONResponse(report, status_code=200 if report["ok"] else 503)
