"""End-to-end: Classify a query, retrieve chunks, and generate a grounded answer."""

import sys
from datetime import datetime

from backend.classify import classify
from backend.alerts import fetch_alerts
from backend.generate import Answer, generate
from backend.planner import plan_trip
from backend.retrieve import retrieve
from backend.schedules import fetch_departures


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
        chunks = fetch_alerts(query) + chunks

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
            chunks = fetch_departures(query, parsed) + chunks

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
