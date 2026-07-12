"""Parse a user query into its intent and trip details."""

import json
import sys
from typing import TypedDict

from openai import OpenAI
from dotenv import load_dotenv

from prompts.loader import load_prompt

# Reads the .env
load_dotenv()

MODEL = "gpt-4o-mini"
VALID_INTENTS = ["route", "alert", "parking-rules", "schedule", "info", "off-topic"]
VALID_DAYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
    "today",
    "tonight",
    "tomorrow",
]
VALID_EDGES = ["first", "last", "both"]

INTENT_SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {"type": "string", "enum": VALID_INTENTS},
        "origin": {"type": ["string", "null"]},
        "destination": {"type": ["string", "null"]},
        "day": {"type": ["string", "null"], "enum": VALID_DAYS + [None]},
        "edge": {"type": ["string", "null"], "enum": VALID_EDGES + [None]},
        "deadline": {"type": ["string", "null"]},
        "reason": {"type": "string"},
    },
    "required": [
        "intent",
        "origin",
        "destination",
        "day",
        "edge",
        "deadline",
        "reason",
    ],
    "additionalProperties": False,
}

SYSTEM_PROMPT = load_prompt("intent.md")


class ParsedQuery(TypedDict):
    """The classifier's read of one query: its domain and trip details."""

    intent: str
    origin: str | None
    destination: str | None
    day: str | None
    edge: str | None
    deadline: str | None
    reason: str


def classify(query: str) -> ParsedQuery:
    """Labels a query with its domain and trip details.

    Args:
        query: The user's question.

    Returns:
        The parsed query: intent + trip details.
    """
    client = OpenAI()
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": query},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "intent_classification",
                "strict": True,
                "schema": INTENT_SCHEMA,
            },
        },
    )
    return json.loads(response.choices[0].message.content)


if __name__ == "__main__":
    print(json.dumps(classify(sys.argv[1]), indent=2))
