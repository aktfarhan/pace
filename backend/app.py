"""The HTTP server: streaming endpoint that answers a query."""

import json
from collections.abc import Iterator

import psycopg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from backend.ask import ask_stream
from data.schema import connect

# Where the frontend runs
ORIGINS = ["http://localhost:3000"]

# The longest askable question
MAX_QUERY = 500

# Proxies buffer a stream unless told not to
STREAM_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}

CHUNK_COUNT = "SELECT count(*) FROM chunks;"

# The server
app = FastAPI(
    title="Pace",
    docs_url="/v1/docs",
    openapi_url="/v1/openapi.json",
    redoc_url=None,
    swagger_ui_oauth2_redirect_url=None,
)

# A browser blocks a call to another port unless the server allows it
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class Question(BaseModel):
    """One question posted to /v1/ask."""

    model_config = ConfigDict(str_strip_whitespace=True)

    query: str = Field(min_length=1, max_length=MAX_QUERY)


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
