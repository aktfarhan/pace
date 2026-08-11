"""End-to-end: Classify a query, retrieve chunks, and generate a grounded answer."""

import sys
from collections.abc import Iterator
from datetime import datetime

from backend.classify import ParsedQuery, classify
from backend.alerts import blocking_alerts, fetch_alerts
from backend.cards import build_card, card_sources
from backend.generate import Answer, generate
from backend.planner.trip import plan_trip
from backend.retrieve import retrieve
from backend.schedules import NO_DEPARTURES, fetch_departures, requested_date

# Midday on the asked date
ALERT_HOUR = 12

# Responses for refusals
REFUSALS = {
    "off-topic": (
        "Pace covers MBTA transit and Boston/Cambridge parking. "
        "That falls outside the scope."
    ),
    "low-confidence": "The available sources don't cover that with enough certainty.",
}

# A stage starting, or the finished answer
Event = tuple[str, dict]


def service_moment(parsed: ParsedQuery) -> str | None:
    """Turns the day a query asks about into a moment to check alerts at.

    Args:
        parsed: The classifier's read of the query.

    Returns:
        A local ISO timestamp on a later date, or None.
    """
    # The date the query asks about, unless that date is today
    now = datetime.now()
    target = requested_date(parsed["day"], now)
    if target is None or target == now.date().isoformat():
        return None

    # That date at midday
    midday = datetime.fromisoformat(target).replace(hour=ALERT_HOUR)
    return midday.astimezone().isoformat()


def refused(reason: str) -> Answer:
    """Builds the answer for refusals.

    Args:
        reason: Reason for refusal.

    Returns:
        A refusal carrying its own wording.
    """
    return {
        "answer": REFUSALS[reason],
        "sources": [],
        "risk": None,
        "should_refuse": True,
        "refuse_reason": reason,
        "card": None,
    }


def ask_stream(query: str) -> Iterator[Event]:
    """Runs the full pipeline.

    Args:
        query: The user's question.

    Yields:
        ("stage", the stage starting) for each step,
        then ("answer", the answer).
    """
    yield ("stage", {"name": "classify"})
    parsed = classify(query)
    intent = parsed["intent"]
    if intent == "off-topic":
        yield ("answer", refused("off-topic"))
        return

    yield ("stage", {"name": "retrieve"})

    # Station-name resolution is off for parking
    chunks = retrieve(query, resolve=(intent != "parking-rules"))

    # Trip answers ground in a computed plan
    if intent == "route":
        yield ("stage", {"name": "plan"})
        plan = plan_trip(query, parsed)
        if not plan:
            yield ("answer", refused("low-confidence"))
            return
        chunks = plan + chunks

    # Alert answers ground in live alerts
    if intent == "alert":
        yield ("stage", {"name": "alerts"})
        chunks = fetch_alerts(query, parsed["route"]) + chunks

    # Schedule answers ground in live departures; leave-by questions in a plan
    if intent == "schedule":
        if parsed["deadline"]:
            yield ("stage", {"name": "plan"})
            plan = plan_trip(query, parsed)
            if not plan:
                yield ("answer", refused("low-confidence"))
                return
            chunks = plan + chunks
        else:
            yield ("stage", {"name": "departures"})
            departures = fetch_departures(parsed)

            # The alert behind an empty schedule
            if not departures or departures[0][0] == NO_DEPARTURES:
                moment = service_moment(parsed)
                departures += blocking_alerts(query, parsed["route"], moment)
            chunks = departures + chunks

    yield ("stage", {"name": "generate"})
    now = datetime.now().isoformat()
    answer = generate(query, chunks, intent, now)

    # The generator refuses with an empty string
    if answer["should_refuse"] and not answer["answer"]:
        yield ("answer", refused("low-confidence"))
        return

    # The card the answer draws
    card = build_card(intent, chunks)
    answer["card"] = card
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
