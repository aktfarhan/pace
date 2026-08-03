"""Places eval: run every query in places.jsonl through resolve() and score it against the expected place."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from backend.geocode import resolve
from data.schema import connect

# Reads the .env
load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
PLACES_PATH = ROOT / "eval" / "places.jsonl"
RUNS_DIR = ROOT / "eval" / "runs"

# One timestamped file per run
run_stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")
output_path = RUNS_DIR / f"places-{run_stamp}.jsonl"

# Build a list of all queries from places.jsonl
queries = []
with PLACES_PATH.open() as places_file:
    for line in places_file:
        if line.strip():
            queries.append(json.loads(line))

total_queries = len(queries)

print(f"Running places eval: {total_queries} queries -> {output_path.name}")

# Tallies for the final summary
correct_count = 0
no_match_total = 0
no_match_correct = 0
error_count = 0
failed_ids = []

run_start = time.perf_counter()
connection = connect()
cursor = connection.cursor()

with output_path.open("w") as output_file:
    for query in queries:
        # A row with nothing expected asks resolve() to return no match
        expects_no_match = not query["expected"]
        if expects_no_match:
            no_match_total += 1

        start_time = time.perf_counter()
        try:
            found = resolve(query["query"], cursor=cursor)
            latency_ms = int((time.perf_counter() - start_time) * 1000)

            # Addresses and streets have no id, use the label as their key
            returned = None
            kind = None
            if found is not None:
                returned = found["place_id"] or found["label"]
                kind = found["kind"]

            is_correct = (
                found is None if expects_no_match else returned in query["expected"]
            )

            result = {
                "query_id": query["id"],
                "query": query["query"],
                "expected": query["expected"],
                "returned": returned,
                "kind": kind,
                "correct": is_correct,
                "latency_ms": latency_ms,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Update tallies
            if is_correct:
                correct_count += 1
                if expects_no_match:
                    no_match_correct += 1
            else:
                failed_ids.append(query["id"])

            marker = "OK" if is_correct else "NO"
            wanted = query["display"]
            label = returned or "no match"
            print(f"  [{query['id']}] {marker} {wanted} -> {label} ({latency_ms}ms)")
        except Exception as error:
            # On failure: clear the transaction, log the error and continue
            connection.rollback()
            error_count += 1
            failed_ids.append(query["id"])
            result = {
                "query_id": query["id"],
                "query": query["query"],
                "expected": query["expected"],
                "error": str(error),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            print(f"  [{query['id']}] ERROR: {error}")

        # Write each row
        output_file.write(json.dumps(result) + "\n")

connection.close()

# Summary block: the headline count, no-match rows, failures, runtime
run_elapsed = time.perf_counter() - run_start

print()
print(f"Correct: {correct_count}/{total_queries}")
print(f"  No match: {no_match_correct}/{no_match_total}")
if error_count:
    print(f"  Errors: {error_count}")
if failed_ids:
    print(f"  Failed: {', '.join(failed_ids)}")
print(f"Runtime: {run_elapsed:.1f}s")
print(f"Output: {output_path}")
