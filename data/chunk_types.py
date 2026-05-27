"""Chunk data types shared by the chunker and the embedder."""

from typing import TypedDict


class StopMetadata(TypedDict):
    """Structured fields for a stop chunk."""

    stop_id: str
    name: str
    lat: float
    lng: float
    routes: list[str]
    vehicle_types: list[int]
    wheelchair_boarding: int
    municipality: str
    zone: str | None
    location_type: int


class RouteMetadata(TypedDict):
    """Structured fields for a route chunk."""

    route_id: str
    short_name: str
    long_name: str
    type: int
    color: str
    fare_class: str
    line: str
    stop_ids: list[str]
    direction_destinations: list[str]
    direction_names: list[str]


class StreetCleaningMetadata(TypedDict):
    """Structured fields for a Boston street-cleaning segment chunk."""

    main_id: int
    street: str
    from_street: str | None
    to_street: str | None
    neighborhood: str | None
    district: str | None
    side: str | None
    start_time: str
    end_time: str
    days: list[str]
    weeks: list[int]
    every_day: bool
    year_round: bool
    one_way: bool
    north_end_pilot: bool
    miles: float


class StopChunk(TypedDict):
    """A stop chunk as written to data/chunks/stops.jsonl by mbta/chunk.py."""

    id: str
    text: str
    metadata: StopMetadata


class RouteChunk(TypedDict):
    """A route chunk as written to data/chunks/routes.jsonl by mbta/chunk.py."""

    id: str
    text: str
    metadata: RouteMetadata


class StreetCleaningChunk(TypedDict):
    """A segment chunk as written to data/chunks/street_cleaning.jsonl."""

    id: str
    text: str
    metadata: StreetCleaningMetadata


type Chunk = StopChunk | RouteChunk | StreetCleaningChunk
