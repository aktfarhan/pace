"""Baseline: run every seed query through gpt-4o-mini with no system prompt"""

import json
import time
from pathlib import Path
from datetime import datetime, timezone

from openai import OpenAI
from dotenv import load_dotenv

# Reads the .env
load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
SEED_PATH = ROOT / "eval" / "seed.jsonl"
RUNS_DIR = ROOT / "eval" / "runs"
MODEL = "gpt-4o-mini"

# Create eval/runs/
RUNS_DIR.mkdir(exist_ok=True)

# Overwrite reruns on the same day, new file otherwise
today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
output_path = RUNS_DIR / f"baseline-{today}.jsonl"

# Read API key
openai_client = OpenAI()

# Build a list of all 30 queries
queries = []
with SEED_PATH.open() as seed_file:
    for line in seed_file:
        if line.strip():
            queries.append(json.loads(line))

print(f"Running baseline: {len(queries)} queries -> {output_path.name}")

with output_path.open("w") as output_file:
    for query in queries:
        start_time = time.perf_counter()
        try:
            # Baseline call with query, at temperature 0
            response = openai_client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": query["query"]}],
                temperature=0,
            )

            latency_ms = int((time.perf_counter() - start_time) * 1000)

            # On success: full response + metadata
            result = {
                "query_id": query["id"],
                "model": MODEL,
                "query": query["query"],
                "response": response.choices[0].message.content,
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "latency_ms": latency_ms,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            print(
                f"  [{query['id']}] {latency_ms}ms {result['input_tokens']} -> {result['output_tokens']} tok"
            )
        except Exception as error:
            # On failure: log the error and continue
            result = {
                "query_id": query["id"],
                "model": MODEL,
                "query": query["query"],
                "error": str(error),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            print(f"  [{query['id']}] ERROR: {error}")

        # Write each row
        output_file.write(json.dumps(result) + "\n")

print(f"Done. Output: {output_path}")
