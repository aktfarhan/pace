"""The HTTP server: streaming endpoint that answers a query."""

import asyncio
import json
import time
from collections.abc import AsyncGenerator, Iterator
from contextlib import asynccontextmanager
from functools import lru_cache

import psycopg
from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from backend.ask import ask_stream
from backend.board import Planned, plan_saved
from backend.lateness import poll
from backend.places import Saved, SavedPlace, add_place, read_places, remove_place
from backend.trips import Kept, SavedTrip, add_trip, read_trips, remove_trip
from backend.risk import warm as warm_model
from backend.status import SystemStatus, read_status, without_alerts
from backend.timetable import warm
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
    watcher = asyncio.create_task(poll())
    try:
        yield
    finally:
        watcher.cancel()


# The server
app = FastAPI(
    title="Pace",
    lifespan=lifespan,
    docs_url="/v1/docs",
    openapi_url="/v1/openapi.json",
    redoc_url=None,
    swagger_ui_oauth2_redirect_url=None,
)

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
    return read_status()


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


@app.get("/v1/health")
def check_health() -> dict:
    """Reports whether the database is reachable.

    Returns:
        The chunk count, or the error that stopped the query.
    """
    try:
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute(CHUNK_COUNT)
            chunks = cursor.fetchone()[0]
    except psycopg.Error as error:
        return {"ok": False, "error": str(error)}
    return {"ok": True, "chunks": chunks}
