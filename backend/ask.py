"""End-to-end: Classify a query, retrieve chunks, and generate a grounded answer."""

import sys
from datetime import datetime

from backend.classify import ParsedQuery, classify
from backend.alerts import blocking_alerts, fetch_alerts
from backend.generate import Answer, generate
from backend.planner.trip import plan_trip
from backend.retrieve import retrieve
from backend.schedules import NO_DEPARTURES, fetch_departures, requested_date

# Midday on the asked date
ALERT_HOUR = 12


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


def ask(query: str) -> Answer:
    """Runs the full pipeline for one query.

    Args:
        query: The user's question.

    Returns:
        The generator's answer JSON.
    """
    parsed = classify(query)
    intent = parsed["intent"]
    if intent == "off-topic":
        return {
            "answer": "",
            "sources": [],
            "risk": None,
            "should_refuse": True,
            "refuse_reason": "off-topic",
        }

    # Station-name resolution is off for parking
    chunks = retrieve(query, resolve=(intent != "parking-rules"))

    # Trip answers ground in a computed plan
    if intent == "route":
        plan = plan_trip(query, parsed)
        if not plan:
            return {
                "answer": "",
                "sources": [],
                "risk": None,
                "should_refuse": True,
                "refuse_reason": "low-confidence",
            }
        chunks = plan + chunks

    # Alert answers ground in live alerts
    if intent == "alert":
        chunks = fetch_alerts(query, parsed["route"]) + chunks

    # Schedule answers ground in live departures; leave-by questions in a plan
    if intent == "schedule":
        if parsed["deadline"]:
            plan = plan_trip(query, parsed)
            if not plan:
                return {
                    "answer": "",
                    "sources": [],
                    "risk": None,
                    "should_refuse": True,
                    "refuse_reason": "low-confidence",
                }
            chunks = plan + chunks
        else:
            departures = fetch_departures(parsed)

            # The alert behind an empty schedule
            if not departures or departures[0][0] == NO_DEPARTURES:
                moment = service_moment(parsed)
                departures += blocking_alerts(query, parsed["route"], moment)
            chunks = departures + chunks

    now = datetime.now().isoformat()
    return generate(query, chunks, intent, now)


if __name__ == "__main__":
    query = sys.argv[1]
    result = ask(query)
    if result["should_refuse"]:
        print(f"[refused: {result['refuse_reason']}]")
    else:
        print(result["answer"])
        print(f"sources: {result['sources']}")
