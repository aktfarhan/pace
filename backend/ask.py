"""End-to-end: Classify a query, retrieve chunks, and generate a grounded answer."""

import sys
from datetime import datetime

from backend.classify import classify
from backend.alerts import fetch_alerts
from backend.generate import Answer, generate
from backend.retrieve import retrieve
from backend.schedules import fetch_departures, has_deadline


def ask(query: str) -> Answer:
    """Runs the full pipeline for one query.

    Args:
        query: The user's question.

    Returns:
        The generator's answer JSON.
    """
    intent = classify(query)
    if intent == "off-topic":
        return {
            "answer": "",
            "sources": [],
            "risk": None,
            "should_refuse": True,
            "refuse_reason": "off-topic",
        }

    # Trips need the planner — refuse until it's built
    if intent == "route":
        return {
            "answer": "",
            "sources": [],
            "risk": None,
            "should_refuse": True,
            "refuse_reason": "low-confidence",
        }

    # Leave-by-a-time questions need travel time — the planner; refuse until then
    if intent == "schedule" and has_deadline(query):
        return {
            "answer": "",
            "sources": [],
            "risk": None,
            "should_refuse": True,
            "refuse_reason": "low-confidence",
        }

    # Station-name resolution is off for parking
    chunks = retrieve(query, resolve=(intent != "parking-rules"))

    # Alert answers ground in live alerts
    if intent == "alert":
        chunks = fetch_alerts(query) + chunks

    # Schedule answers ground in live departures
    if intent == "schedule":
        chunks = fetch_departures(query) + chunks

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
