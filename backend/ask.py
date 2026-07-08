"""End-to-end: Classify a query, retrieve chunks, and generate a grounded answer."""

import sys
from datetime import datetime

from backend.classify import classify
from backend.generate import Answer, generate
from backend.retrieve import retrieve


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

    chunks = retrieve(query)
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
