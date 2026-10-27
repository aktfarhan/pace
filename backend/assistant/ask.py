"""End-to-end: Classify a query, retrieve chunks, and generate a grounded answer."""

import sys
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import httpx

from backend.assistant.parse import ParsedQuery
from backend.core.clock import ZONE, now_in_boston
from backend.mbta.alerts import blocking_alerts, fetch_alerts
from backend.mbta.stations import find_stations
from backend.assistant.cards import (
    Picked,
    Spot,
    TripCard,
    build_card,
    card_sources,
    choices_card,
    trip_card,
)
from backend.assistant.generate import Answer, generate
from backend.planner.trip import ends_only, plan_trip
from backend.assistant.llm import llm
from backend.assistant.retrieve import Row, embed_query, retrieve
from backend.geo.streets import Place
from backend.reliability.risk import risk_for
from backend.mbta.schedules import (
    NO_DEPARTURES,
    fetch_departures,
    live_departures,
    requested_date,
)
from backend.planner.timetable import service_date_at
from backend.saved.keywords import name_key, read_with_saved
from backend.saved.places import saved_spots

# Midday on the asked date
ALERT_HOUR = 12

# Responses for refusals
REFUSALS = {
    "off-topic": "Pace covers MBTA transit. That falls outside the scope.",
    "low-confidence": "The available sources don't cover that with enough certainty.",
}

# A stage starting, or the finished answer
Event = tuple[str, dict]

# Makes the search embedding while the classifier reads the question
_embedder = ThreadPoolExecutor(max_workers=8, thread_name_prefix="embed")


def service_moment(parsed: ParsedQuery) -> str | None:
    """Turns the day a query asks about into a moment to check alerts at.

    Args:
        parsed: The classifier's read of the query.

    Returns:
        A Boston ISO timestamp on a later date, or None.
    """
    # The date the query asks about, unless that date is today
    now = now_in_boston()
    target = requested_date(parsed["day"], now)
    if target is None or target == service_date_at(now).isoformat():
        return None

    # That date at midday
    midday = datetime.fromisoformat(target).replace(hour=ALERT_HOUR, tzinfo=ZONE)
    return midday.isoformat()


def named_stations(parsed: ParsedQuery, saved: dict) -> list[str]:
    """Finds the stations the question's places name.

    Args:
        parsed: The read of the query.
        saved: The user's saved name keys.

    Returns:
        Station ids, origin first.
    """
    ids = []
    for place in (parsed["origin"], parsed["destination"]):
        if place in saved:
            continue
        for station in find_stations(place):
            if station["id"] not in ids:
                ids.append(station["id"])
    return ids


def refused(reason: str, intent: str) -> Answer:
    """Builds the answer for refusals.

    Args:
        reason: Reason for refusal.
        intent: The query's domain label.

    Returns:
        A refusal carrying its own wording.
    """
    return {
        "answer": REFUSALS[reason],
        "intent": intent,
        "sources": [],
        "risk": None,
        "chance": None,
        "should_refuse": True,
        "refuse_reason": reason,
        "card": None,
    }


def unfound(plan: list, intent: str) -> Answer:
    """Builds the answer for a trip end that couldn't be found.

    Args:
        plan: The planner's unfound row.
        intent: The query's domain label.

    Returns:
        The planner's own words, with places to pick from.
    """
    return {
        "answer": plan[0][2],
        "intent": intent,
        "sources": [],
        "risk": None,
        "chance": None,
        "should_refuse": False,
        "refuse_reason": None,
        "card": choices_card(plan),
    }


def with_next_trains(card: TripCard, chunks: list[Row]) -> None:
    """Adds the next live departures to each ride on a trip card.

    Args:
        card: The trip card, changed in place.
        chunks: The rows the card was built from.
    """
    rides = []
    for leg in card["legs"]:
        if leg["kind"] == "ride":
            rides.append(leg)

    # The plan's ride rows come in the same order as the card's rides
    index = 0
    try:
        for _, kind, _, metadata, _ in chunks:
            if kind == "plan" and "route_id" in metadata and index < len(rides):
                rides[index]["next_departures"] = live_departures(
                    metadata["route_id"],
                    metadata["board_stop"],
                    metadata["alight_stop"],
                )
                index += 1
    except httpx.HTTPError:
        pass


def again_for(query: str, parsed: ParsedQuery, card: TripCard) -> Picked:
    """Shapes a planned trip so it can be planned again without the question.

    Args:
        query: The user's question.
        parsed: The read of the query.
        card: The trip card.

    Returns:
        The trip with both ends as found.
    """
    origin_lat, origin_lon = card["origin_at"]
    end_lat, end_lon = card["destination_at"]
    return {
        "query": query,
        "origin": Spot(label=card["origin"], lat=origin_lat, lon=origin_lon),
        "destination": Spot(label=card["destination"], lat=end_lat, lon=end_lon),
        "day": parsed["day"],
        "deadline": parsed["deadline"],
        "leave_at": parsed.get("leave_at"),
    }


def plan_picked(pick: Picked, code: str | None = None) -> Answer:
    """Plans a trip whose ends were picked, with no question to read.

    Args:
        pick: The trip, each end as text or a spot.
        code: The user's code.

    Returns:
        The trip's answer, or places to pick from.
    """
    saved = saved_spots(code)

    # A spot stands in for its end's text
    ends = []
    for end in (pick["origin"], pick["destination"]):
        if isinstance(end, str):
            ends.append(end)
            continue
        ends.append(end["label"])
        saved[name_key(end["label"])] = Place(
            place_id=None,
            label=end["label"],
            kind="picked",
            lat=end["lat"],
            lon=end["lon"],
        )

    parsed = ends_only(
        ends[0], ends[1], pick["day"], pick["deadline"], pick["leave_at"]
    )
    plan = plan_trip(pick["query"], parsed, saved=saved)
    if not plan:
        return refused("low-confidence", "route")
    if plan[0][0] == "plan:unfound":
        return unfound(plan, "route")

    # The planner's own words stand in for a written answer
    card = trip_card(plan)
    found = None
    if card is not None:
        with_next_trains(card, plan)
        found = risk_for(plan, now_in_boston())
    return {
        "answer": plan[0][2],
        "intent": "route",
        "sources": sorted(card_sources(card)),
        "risk": found["level"] if found else None,
        "chance": found["chance"] if found else None,
        "should_refuse": False,
        "refuse_reason": None,
        "card": card,
        "again": again_for(pick["query"], parsed, card) if card else None,
    }


def ask_stream(query: str, code: str | None = None) -> Iterator[Event]:
    """Runs the full pipeline.

    Args:
        query: The user's question.
        code: The user's code.

    Yields:
        ("stage", the stage starting) for each step,
        then ("answer", the answer).
    """
    yield ("stage", {"name": "classify"})
    embedding = _embedder.submit(embed_query, llm(), query)
    saved = saved_spots(code)
    parsed = read_with_saved(query, saved)
    intent = parsed["intent"]
    if intent == "off-topic":
        yield ("answer", refused("off-topic", intent))
        return

    yield ("stage", {"name": "retrieve"})
    stations = named_stations(parsed, saved)
    chunks = retrieve(query, vector=embedding.result(), stations=stations)

    # Trip answers ground in a computed plan
    if intent == "route":
        yield ("stage", {"name": "plan"})
        plan = plan_trip(query, parsed, saved=saved)
        if not plan:
            yield ("answer", refused("low-confidence", intent))
            return

        # A place that wasn't found needs no written answer
        if plan[0][0] == "plan:unfound":
            yield ("answer", unfound(plan, intent))
            return
        chunks = plan + chunks

    # Alert answers ground in live alerts
    if intent == "alert":
        yield ("stage", {"name": "alerts"})
        chunks = fetch_alerts(stations, parsed["route"]) + chunks

    # Schedule answers ground in departures; leave-by questions in a plan
    if intent == "schedule":
        if parsed["deadline"] and parsed["destination"]:
            yield ("stage", {"name": "plan"})
            plan = plan_trip(query, parsed, saved=saved)
            if not plan:
                yield ("answer", refused("low-confidence", intent))
                return
            if plan[0][0] == "plan:unfound":
                yield ("answer", unfound(plan, intent))
                return
            chunks = plan + chunks
        else:
            yield ("stage", {"name": "departures"})
            departures = fetch_departures(parsed)

            # The alert behind an empty schedule
            if not departures or departures[0][0] == NO_DEPARTURES:
                moment = service_moment(parsed)
                departures += blocking_alerts(stations, parsed["route"], moment)
            chunks = departures + chunks

    yield ("stage", {"name": "generate"})
    now = now_in_boston().isoformat()
    answer = generate(query, chunks, intent, now)

    # The generator refuses with an empty string
    if answer["should_refuse"] and not answer["answer"]:
        yield ("answer", refused("low-confidence", intent))
        return

    # The card the answer draws
    card = build_card(intent, chunks)

    # Trip cards get the next trains for each ride
    if card is not None and card["kind"] == "trip":
        with_next_trains(card, chunks)
        answer["again"] = again_for(query, parsed, card)

    answer["card"] = card

    # The risk pill and the chance beside it
    found = risk_for(chunks, now_in_boston())
    answer["risk"] = found["level"] if found else None
    answer["chance"] = found["chance"] if found else None

    answer["sources"] = sorted(set(answer["sources"]) | card_sources(card))
    yield ("answer", answer)


def ask(query: str) -> Answer:
    """Runs the full pipeline for one query.

    Args:
        query: The user's question.

    Returns:
        The generator's answer JSON.
    """
    for kind, payload in ask_stream(query):
        if kind == "answer":
            return payload


if __name__ == "__main__":
    query = sys.argv[1]
    result = ask(query)
    if result["should_refuse"]:
        print(result["answer"])
        print(f"[{result['refuse_reason']}]")
    else:
        print(result["answer"])
        print(f"sources: {result['sources']}")
