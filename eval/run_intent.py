"""Intent classifier: run every seed query through gpt-4o-mini using prompts/intent.md as system prompt; score against the gold domain label"""

import json
import re
import time
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

from openai import OpenAI
from dotenv import load_dotenv

# Reads the .env
load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
SEED_PATH = ROOT / "eval" / "seed.jsonl"
PROMPT_PATH = ROOT / "prompts" / "intent.md"
RUNS_DIR = ROOT / "eval" / "runs"
MODEL = "gpt-4o-mini"
VALID_INTENTS = [
    "route",
    "alert",
    "parking-rules",
    "schedule",
    "off-topic",
]

# gpt-4o-mini cost per 1M tokens
INPUT_COST_PER_1M = 0.15
OUTPUT_COST_PER_1M = 0.60

# The model output schema
INTENT_SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {"type": "string", "enum": VALID_INTENTS},
        "reason": {"type": "string"},
    },
    "required": ["intent", "reason"],
    "additionalProperties": False,
}


def strip_frontmatter(text: str) -> str:
    """Remove a leading --- YAML --- block."""
    match = re.match(r"^---\r?\n.*?\r?\n---\r?\n(.*)$", text, re.DOTALL)
    return match.group(1).strip() if match else text.strip()


def classify_deterministic(query):
    """Rules that bypass the LLM."""
    if query.get("image"):
        return "parking-sign", "image attached"
    return None


# Create eval/runs/
RUNS_DIR.mkdir(exist_ok=True)

# Overwrite reruns on the same day, new file otherwise
today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
output_path = RUNS_DIR / f"intent-{today}.jsonl"

# Load intent.md and drop its YAML header
system_prompt = strip_frontmatter(PROMPT_PATH.read_text())

# Read API key
openai_client = OpenAI()

# Build a list of all queries from seed.jsonl
queries = []
with SEED_PATH.open() as seed_file:
    for line in seed_file:
        if line.strip():
            queries.append(json.loads(line))

total_queries = len(queries)

print(f"Running intent classifier: {total_queries} queries -> {output_path.name}")

# Tallies for the final summary
correct_count = 0
refusal_count = 0
json_error_count = 0
total_input_tokens = 0
total_output_tokens = 0
invalid_intent_count = 0
domain_counts = defaultdict(lambda: {"correct": 0, "total": 0})

run_start = time.perf_counter()

with output_path.open("w") as output_file:
    for query in queries:
        gold_intent = query["domain"]

        deterministic = classify_deterministic(query)
        if deterministic:
            predicted_intent, reason = deterministic
            is_correct = predicted_intent == gold_intent
            result = {
                "query_id": query["id"],
                "model": "deterministic",
                "query": query["query"],
                "gold_intent": gold_intent,
                "predicted_intent": predicted_intent,
                "reason": reason,
                "correct": is_correct,
                "json_error": False,
                "invalid_intent": False,
                "refusal": None,
                "raw_response": None,
                "input_tokens": 0,
                "output_tokens": 0,
                "latency_ms": 0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Update Tallies
            domain_counts[gold_intent]["total"] += 1
            if is_correct:
                correct_count += 1
                domain_counts[gold_intent]["correct"] += 1
            marker = "OK" if is_correct else "NO"

            print(
                f"  [{query['id']}] {marker} {gold_intent} -> {predicted_intent} (deterministic)"
            )
            output_file.write(json.dumps(result) + "\n")
            continue

        start_time = time.perf_counter()
        try:
            # Intent call: system prompt + user query, with structured output schema
            response = openai_client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query["query"]},
                ],
                temperature=0,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "intent_classification",
                        "strict": True,
                        "schema": INTENT_SCHEMA,
                    },
                },
            )

            latency_ms = int((time.perf_counter() - start_time) * 1000)
            message = response.choices[0].message

            # Output values
            reason = ""
            predicted_intent = None

            # Three failure modes
            json_error = False
            invalid_intent = False
            refusal = message.refusal

            if refusal:
                # Model declined to answer
                refusal_count += 1
            elif message.content:
                # Process the message
                try:
                    parsed = json.loads(message.content)
                    predicted_intent = parsed.get("intent")
                    reason = parsed.get("reason", "")
                    if predicted_intent not in VALID_INTENTS:
                        invalid_intent = True
                        invalid_intent_count += 1
                except json.JSONDecodeError:
                    json_error = True
                    json_error_count += 1
            else:
                # No content and no refusal
                json_error = True
                json_error_count += 1

            is_correct = predicted_intent == gold_intent

            total_input_tokens += response.usage.prompt_tokens
            total_output_tokens += response.usage.completion_tokens

            # On success: full response + metadata
            result = {
                "query_id": query["id"],
                "model": response.model,
                "query": query["query"],
                "gold_intent": gold_intent,
                "predicted_intent": predicted_intent,
                "reason": reason,
                "correct": is_correct,
                "json_error": json_error,
                "invalid_intent": invalid_intent,
                "refusal": refusal,
                "raw_response": message.content,
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "latency_ms": latency_ms,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Update Tallies
            domain_counts[gold_intent]["total"] += 1
            if is_correct:
                correct_count += 1
                domain_counts[gold_intent]["correct"] += 1

            marker = "OK" if is_correct else "NO"
            print(
                f"  [{query['id']}] {marker} {gold_intent} -> {predicted_intent} "
                f"({latency_ms}ms, {response.usage.completion_tokens} tok)"
            )
        except Exception as error:
            # On failure: log the error and continue
            result = {
                "query_id": query["id"],
                "model": MODEL,
                "query": query["query"],
                "gold_intent": gold_intent,
                "error": str(error),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            domain_counts[gold_intent]["total"] += 1
            print(f"  [{query['id']}] ERROR: {error}")

        # Write each row
        output_file.write(json.dumps(result) + "\n")

# Summary block: overall + per-domain accuracy, total tokens, total cost, runtime
run_elapsed = time.perf_counter() - run_start
input_cost = total_input_tokens / 1_000_000 * INPUT_COST_PER_1M
output_cost = total_output_tokens / 1_000_000 * OUTPUT_COST_PER_1M
total_cost = input_cost + output_cost
accuracy_pct = 100 * correct_count / total_queries

print()
print(f"Overall: {correct_count}/{total_queries} correct ({accuracy_pct:.1f}%)")
if json_error_count:
    print(f"  JSON errors: {json_error_count}")
if invalid_intent_count:
    print(f"  Invalid intents: {invalid_intent_count}")
if refusal_count:
    print(f"  Refusals: {refusal_count}")

print()
print("Per-domain accuracy:")
for domain, counts in sorted(domain_counts.items()):
    pct = 100 * counts["correct"] / counts["total"] if counts["total"] else 0
    print(f"  {domain:16s} {counts['correct']}/{counts['total']} ({pct:.1f}%)")

print()
print(f"Tokens: {total_input_tokens} in, {total_output_tokens} out")
print(f"Cost: ${total_cost:.4f}")
print(f"Runtime: {run_elapsed:.1f}s")
print(f"Output: {output_path}")
