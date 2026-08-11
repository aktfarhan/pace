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


type Card = DeparturesCard


def card_sources(card: Card | None) -> set[str]:
    """Collects every chunk id a card stands on.

    Args:
        card: The card an answer draws, or None.

    Returns:
        The ids the card cites.
    """
    if card is None:
        return set()
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


def build_card(intent: str, chunks: list[Row]) -> Card | None:
    """Picks the card an answer of this intent carries.

    Args:
        intent: The query's domain label.
        chunks: The rows the answer stands on.

    Returns:
        The card, or None when the intent has no card.
    """
    if intent == "schedule":
        return departures_card(chunks)
    return None


if __name__ == "__main__":
    from backend.classify import classify
    from backend.schedules import fetch_departures

    query = sys.argv[1]
    parsed = classify(query)
    card = build_card(parsed["intent"], fetch_departures(parsed))
    print(json.dumps(card, indent=2))
