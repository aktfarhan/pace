"""Assemble the structured card an answer carries."""

import json
import sys
from datetime import datetime
from typing import Literal, TypedDict

from backend.retrieve import Row


class Departure(TypedDict):
    """One route leaving one stop in one direction."""

    source: str
    route_id: str
    short_name: str
    label: str
    route_type: int
    color: str
    station: str
    destination: str
    times: list[str]
    live: bool


class DeparturesCard(TypedDict):
    """What is leaving a stop, soonest first."""

    kind: Literal["departures"]
    departures: list[Departure]
    retrieved_at: str


class WalkLeg(TypedDict):
    """One walk, or a transfer inside a station."""

    kind: Literal["walk"]
    source: str
    destination: str
    transfer: bool
    depart: str
    arrive: str


class RideLeg(TypedDict):
    """One ride from boarding to alighting."""

    kind: Literal["ride"]
    source: str
    route_id: str
    label: str
    destination: str
    depart: str
    arrive: str


class TripCard(TypedDict):
    """One planned trip."""

    kind: Literal["trip"]
    origin: str
    destination: str
    depart: str
    arrive: str
    transfers: int
    live: bool
    legs: list[WalkLeg | RideLeg]
    retrieved_at: str


type Card = DeparturesCard | TripCard


def card_sources(card: Card | None) -> set[str]:
    """Collects every chunk id a card stands on.

    Args:
        card: The card an answer draws, or None.

    Returns:
        The ids the card cites.
    """
    if card is None:
        return set()
    if card["kind"] == "trip":
        sources = {"plan:summary"}
        for leg in card["legs"]:
            sources.add(leg["source"])
        return sources
    return {departure["source"] for departure in card["departures"]}


def departures_card(chunks: list[Row]) -> DeparturesCard | None:
    """Builds the card a next-departures answer carries.

    Args:
        chunks: The rows the answer stands on.

    Returns:
        The card, or None.
    """
    departures: list[Departure] = []
    retrieved_at = ""
    for chunk_id, kind, _, metadata, _ in chunks:
        if kind != "schedule":
            continue
        if metadata.get("edge") is not None or "departure_times" not in metadata:
            return None

        retrieved_at = metadata["retrieved_at"]
        departures.append(
            {
                "source": chunk_id,
                "route_id": metadata["route_id"],
                "short_name": metadata["short_name"],
                "label": metadata["label"],
                "route_type": metadata["route_type"],
                "color": metadata["color"],
                "station": metadata["station"],
                "destination": metadata["destination"],
                "times": metadata["departure_times"],
                "live": metadata["live"],
            }
        )

    if not departures:
        return None

    # Soonest first, across every route at the stop
    departures.sort(key=lambda departure: datetime.fromisoformat(departure["times"][0]))
    return {
        "kind": "departures",
        "departures": departures,
        "retrieved_at": retrieved_at,
    }


def trip_card(chunks: list[Row]) -> TripCard | None:
    """Builds the card a trip-plan answer carries.

    Args:
        chunks: The rows the answer is on.

    Returns:
        The card, or None.
    """
    summary = None
    legs: list[WalkLeg | RideLeg] = []
    for chunk_id, kind, _, metadata, _ in chunks:
        if kind != "plan":
            continue

        if chunk_id == "plan:none":
            return None

        if chunk_id == "plan:summary":
            summary = metadata
            continue

        if "route_id" in metadata:
            legs.append(
                {
                    "kind": "ride",
                    "source": chunk_id,
                    "route_id": metadata["route_id"],
                    "label": metadata["label"],
                    "destination": metadata["alight_station"],
                    "depart": metadata["depart"],
                    "arrive": metadata["arrive"],
                }
            )
        else:
            legs.append(
                {
                    "kind": "walk",
                    "source": chunk_id,
                    "destination": metadata["to"],
                    "transfer": metadata["from"] == metadata["to"],
                    "depart": metadata["depart"],
                    "arrive": metadata["arrive"],
                }
            )

    if summary is None or not legs:
        return None

    return {
        "kind": "trip",
        "origin": summary["origin_label"],
        "destination": summary["destination_label"],
        "depart": summary["depart"],
        "arrive": summary["arrive"],
        "transfers": summary["transfers"],
        "live": summary["live"],
        "legs": legs,
        "retrieved_at": summary["retrieved_at"],
    }


def build_card(intent: str, chunks: list[Row]) -> Card | None:
    """Picks the card an answer of this intent carries.

    Args:
        intent: The query's domain label.
        chunks: The rows the answer stands on.

    Returns:
        The card, or None when the intent has no card.
    """
    if intent == "route":
        return trip_card(chunks)

    # Leave-by questions have a plan instead of departures
    if intent == "schedule":
        return trip_card(chunks) or departures_card(chunks)
    return None


if __name__ == "__main__":
    from backend.classify import classify
    from backend.planner.trip import plan_trip
    from backend.schedules import fetch_departures

    query = sys.argv[1]
    parsed = classify(query)
    if parsed["intent"] == "route" or parsed["deadline"]:
        chunks = plan_trip(query, parsed)
    else:
        chunks = fetch_departures(parsed)
    card = build_card(parsed["intent"], chunks)
    print(json.dumps(card, indent=2))
