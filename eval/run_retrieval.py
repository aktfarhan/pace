"""Retrieval eval: run every query in retrieval.jsonl through retrieve() and score Recall@1 and Recall@5 against the expected chunk ids."""

import json
import time
from pathlib import Path
from datetime import datetime, timezone

from dotenv import load_dotenv

from backend.retrieve import retrieve

# Reads the .env
load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
RETRIEVAL_PATH = ROOT / "eval" / "retrieval.jsonl"
RUNS_DIR = ROOT / "eval" / "runs"

# One timestamped file per run
run_stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")
output_path = RUNS_DIR / f"retrieval-{run_stamp}.jsonl"

# Build a list of all queries from retrieval.jsonl
queries = []
with RETRIEVAL_PATH.open() as retrieval_file:
    for line in retrieval_file:
        if line.strip():
            queries.append(json.loads(line))

total_queries = len(queries)

print(f"Running retrieval eval: {total_queries} queries -> {output_path.name}")

# Tallies for the final summary
hit1_count = 0
hit5_count = 0
error_count = 0
failed_ids = []

run_start = time.perf_counter()

with output_path.open("w") as output_file:
    for query in queries:
        start_time = time.perf_counter()
        try:
            # Retrieval call with the row's resolve flag
            returned = retrieve(query["query"], resolve=query["resolve"])
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            returned_ids = [chunk[0] for chunk in returned]

            # Rank of the first expected chunk, 1-based; None when absent
            rank = None
            for position, chunk_id in enumerate(returned_ids, 1):
                if chunk_id in query["expected"]:
                    rank = position
                    break

            hit1 = rank == 1
            hit5 = rank is not None

            result = {
                "query_id": query["id"],
                "query": query["query"],
                "expected": query["expected"],
                "returned_ids": returned_ids,
                "rank": rank,
                "hit1": hit1,
                "hit5": hit5,
                "latency_ms": latency_ms,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Update tallies
            if hit1:
                hit1_count += 1
            if hit5:
                hit5_count += 1
            else:
                failed_ids.append(query["id"])

            marker = "OK" if hit5 else "NO"
            rank_label = f"rank {rank}" if rank else "miss"
            print(f"  [{query['id']}] {marker} {rank_label} ({latency_ms}ms)")
        except Exception as error:
            # On failure: log the error and continue
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

# Summary block: Recall@1, Recall@5, failures, runtime
run_elapsed = time.perf_counter() - run_start

print()
print(f"Recall@1: {hit1_count}/{total_queries}")
print(f"Recall@5: {hit5_count}/{total_queries}")
if error_count:
    print(f"  Errors: {error_count}")
if failed_ids:
    print(f"  Failed: {', '.join(failed_ids)}")
print(f"Runtime: {run_elapsed:.1f}s")
print(f"Output: {output_path}")
