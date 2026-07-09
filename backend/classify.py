"""Classify a user query into an intent."""

import json
import sys

from openai import OpenAI
from dotenv import load_dotenv

from prompts.loader import load_prompt

# Reads the .env
load_dotenv()

MODEL = "gpt-4o-mini"
VALID_INTENTS = ["route", "alert", "parking-rules", "schedule", "info", "off-topic"]

INTENT_SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {"type": "string", "enum": VALID_INTENTS},
        "reason": {"type": "string"},
    },
    "required": ["intent", "reason"],
    "additionalProperties": False,
}

SYSTEM_PROMPT = load_prompt("intent.md")


def classify(query: str) -> str:
    """Returns the intent label for a query.

    Args:
        query: The user's question.

    Returns:
        One of VALID_INTENTS.
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

    parsed = json.loads(response.choices[0].message.content)
    return parsed["intent"]


if __name__ == "__main__":
    print(classify(sys.argv[1]))
