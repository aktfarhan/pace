"""Answer eval: run every text seed query through the full ask() pipeline and score answer-or-refuse against the expected action."""

import json
import time
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

from dotenv import load_dotenv

from backend.ask import ask

# Reads the .env
load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
SEED_PATH = ROOT / "eval" / "seed.jsonl"
RUNS_DIR = ROOT / "eval" / "runs"

# Domains whose data layer isn't built yet
NOT_BUILT = {"route", "parking-rules"}

# One timestamped file per run
run_stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")
output_path = RUNS_DIR / f"answers-{run_stamp}.jsonl"

# Build a list of text queries from seed.jsonl; sign queries need images
queries = []
with SEED_PATH.open() as seed_file:
    for line in seed_file:
        if line.strip():
            row = json.loads(line)
            if not row.get("image"):
                queries.append(row)

total_queries = len(queries)

print(f"Running answer eval: {total_queries} queries -> {output_path.name}")

# Tallies for the final summary
correct_count = 0
error_count = 0
failed_ids = []
domain_counts = defaultdict(lambda: {"correct": 0, "total": 0})

run_start = time.perf_counter()

with output_path.open("w") as output_file:
    for query in queries:
        domain = query["domain"]
        expected = "refuse" if domain in NOT_BUILT else query["expected_action"]

        start_time = time.perf_counter()
        try:
            answer = ask(query["query"])
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            action = "refuse" if answer["should_refuse"] else "answer"
            is_correct = action == expected

            result = {
                "query_id": query["id"],
                "query": query["query"],
                "domain": domain,
                "expected_action": expected,
                "action": action,
                "correct": is_correct,
                "answer": answer["answer"],
                "sources": answer["sources"],
                "refuse_reason": answer["refuse_reason"],
                "latency_ms": latency_ms,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Update tallies
            domain_counts[domain]["total"] += 1
            if is_correct:
                correct_count += 1
                domain_counts[domain]["correct"] += 1
            else:
                failed_ids.append(query["id"])

            marker = "OK" if is_correct else "NO"
            print(f"  [{query['id']}] {marker} {expected} -> {action} ({latency_ms}ms)")
        except Exception as error:
            # On failure: log the error and continue
            error_count += 1
            failed_ids.append(query["id"])
            result = {
                "query_id": query["id"],
                "query": query["query"],
                "domain": domain,
                "expected_action": expected,
                "error": str(error),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            domain_counts[domain]["total"] += 1
            print(f"  [{query['id']}] ERROR: {error}")

        # Write each row
        output_file.write(json.dumps(result) + "\n")

# Summary block: overall + per-domain accuracy, failures, runtime
run_elapsed = time.perf_counter() - run_start
accuracy_pct = 100 * correct_count / total_queries

print()
print(f"Overall: {correct_count}/{total_queries} correct ({accuracy_pct:.1f}%)")
if error_count:
    print(f"  Errors: {error_count}")
if failed_ids:
    print(f"  Failed: {', '.join(failed_ids)}")

print()
print("Per-domain accuracy:")
for domain, counts in sorted(domain_counts.items()):
    pct = 100 * counts["correct"] / counts["total"] if counts["total"] else 0
    print(f"  {domain:16s} {counts['correct']}/{counts['total']} ({pct:.1f}%)")

print()
print(f"Runtime: {run_elapsed:.1f}s")
print(f"Output: {output_path}")
