"""Generate a grounded, cited answer from a query and its retrieved chunks."""

import json
import sys
from datetime import datetime
from typing import TypedDict

from openai import OpenAI
from dotenv import load_dotenv

from backend.retrieve import Row, retrieve
from prompts.loader import load_prompt

# Reads the .env
load_dotenv()

MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = load_prompt("generate.md")


class Answer(TypedDict):
    """The generator's structured answer"""

    answer: str
    sources: list[str]
    risk: str | None
    should_refuse: bool
    refuse_reason: str | None


def generate(
    query: str, chunks: list[Row], intent: str, now: str, risk: str | None = None
) -> Answer:
    """Produces a grounded, cited answer from retrieved chunks.

    Args:
        query: The user's question.
        chunks: Retrieved rows (id, kind, text, metadata, distance).
        intent: The query's domain label.
        now: Current time, ISO 8601.
        risk: Route risk label, or None.

    Returns:
        The parsed answer JSON (answer, sources, risk, should_refuse,
        refuse_reason). An answer citing a chunk that was never provided
        comes back as a refusal.
    """
    # Shape the chunks the way generate.md expects
    chunk_inputs = []
    for chunk_id, kind, text, metadata, distance in chunks:
        chunk_inputs.append({"id": chunk_id, "score": distance, "content": text})

    inputs = {
        "query": query,
        "intent": intent,
        "chunks": chunk_inputs,
        "risk": risk,
        "now": now,
    }

    client = OpenAI()
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(inputs)},
        ],
        response_format={"type": "json_object"},
    )
    result: Answer = json.loads(response.choices[0].message.content)

    # A cited source that was never retrieved means the answer is invented
    chunk_ids = {chunk["id"] for chunk in chunk_inputs}
    for source in result["sources"]:
        if source not in chunk_ids:
            return {
                "answer": "",
                "sources": [],
                "risk": None,
                "should_refuse": True,
                "refuse_reason": "low-confidence",
            }
    return result


if __name__ == "__main__":
    query = sys.argv[1]
    chunks = retrieve(query)
    now = datetime.now().isoformat()
    result = generate(query, chunks, intent="route", now=now)
    print(json.dumps(result, indent=2))
