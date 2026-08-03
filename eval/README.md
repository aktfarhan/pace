# eval/

The evaluation set.

---

## Seed schema

Each line in `seed.jsonl` is one query in JSON:

```
{
  "id": "q-0042",
  "query": "yo when should i leave to make my 10am at south station",
  "domain": "schedule",
  "style": "casual",
  "gold_answer": "Leave around 9:25 if the Red Line is clear; earlier if alerts indicate signal issues.",
  "gold_sources": ["mbta://schedules/red"],
  "expected_action": "answer",
  "expected_risk": "mid",
  "notes": "tests schedule-aware mode with a casual prompt"
}
```

Fields:

| Field             | Values                                                                                         |
| ----------------- | ---------------------------------------------------------------------------------------------- |
| `id`              | unique string                                                                                  |
| `query`           | the user-facing question                                                                       |
| `domain`          | `route` \| `alert` \| `parking-rules` \| `parking-sign` \| `schedule` \| `info` \| `off-topic` |
| `style`           | `formal` \| `casual` \| `typo` \| `abbrev` \| `adversarial`                                    |
| `gold_answer`     | reference answer for LLM-as-judge scoring                                                      |
| `gold_sources`    | canonical sources that should appear in citations                                              |
| `expected_action` | `answer` \| `refuse` \| `clarify`                                                              |
| `expected_risk`   | `low` \| `mid` \| `high` \| `n/a`                                                              |
| `notes`           | author commentary                                                                              |

Parking sign queries also include `image: "signs/0042.jpg"`.

---

## Distribution policy

| Domain        | Share |
| ------------- | ----- |
| route         | 30%   |
| alert         | 15%   |
| parking-rules | 15%   |
| schedule      | 15%   |
| info          | 10%   |
| parking-sign  | 10%   |
| off-topic     | 5%    |

Within each domain, writing styles mix as:

- 50% casual
- 25% formal
- 15% abbreviations or typos
- 10% adversarial (prompt injection, slurs, ambiguous, multi-question)

---

## Retrieval set

Each line in `retrieval.jsonl` is one retrieval check: the expected chunk should come back in the top 5.

```
{
  "id": "r-0001",
  "query": "what buses stop at central",
  "expected": ["stop:place-cntsq"],
  "resolve": true,
  "notes": "2026-07-10: ranked below 20; Lynn 426 and suburban Central St stops won"
}
```

Fields:

| Field      | Values                                              |
| ---------- | --------------------------------------------------- |
| `id`       | unique string                                       |
| `query`    | the user-facing question                            |
| `expected` | chunk ids that answer the query; hit if any returns |
| `resolve`  | station-name resolution on or off                   |
| `notes`    | author commentary                                   |

Run with `python -m eval.run_retrieval`. Target is 100% at Recall@5. Re-run after any retrieval change.

---

## Places set

Each line in `places.jsonl` is one typed destination and the place it points to.

```
{
  "id": "p-0037",
  "query": "riverside",
  "expected": ["osm:way:487815858", "station:place-river"],
  "display": "Riverside",
  "notes": "2026-08-01: eleven towns hold one. Cambridge sits 4.5 km out and Newton 16 km, so the kind bonus has to survive the distance penalty. Guards the NEIGHBORHOOD_NAMED ordering fix"
}
```

Fields:

| Field      | Values                                                |
| ---------- | ----------------------------------------------------- |
| `id`       | unique string                                         |
| `query`    | what the user typed                                   |
| `expected` | place ids that answer the query; empty means no match |
| `display`  | the answer in words, for reading a failure            |
| `notes`    | author commentary                                     |

`expected` holds root ids, with the alias index dropped. Addresses and streets have no id, so their label is the key. Every id naming the same physical point is listed.

Rows with an empty `expected` are scored on their own line, so a change that widens matching cannot hide inside the headline count.

Run with `python -m eval.run_places`. Re-run after any change to ranking, normalization, or the places data.

---

## Answer set

`run_answers.py` runs every text query in `seed.jsonl` through the full pipeline and checks: answered when it should answer, refused when it should refuse.

Expected action comes from `expected_action`, except domains listed in `NOT_BUILT` inside the runner — their data layer doesn't exist yet, so refusing is correct until it ships. Skips `image` queries until the sign reader exists.

Run with `python -m eval.run_answers`. Re-run after any prompt change.

---

## Splits

- `seed.jsonl` — dev set, tune freely
- `retrieval.jsonl` — retrieval checks, re-run after any retrieval change
- `places.jsonl` — destination resolution, re-run after any ranking or places-data change
- `holdout.jsonl` — final-number set, never tuned against
- `signs/` — parking sign photos + `signs/labels.jsonl`

---

## Metrics + targets

| Metric                    | Target   |
| ------------------------- | -------- |
| Recall@1                  | > 0.75   |
| Recall@5                  | > 0.90   |
| Faithfulness (RAGAS)      | > 0.90   |
| Answer correctness        | > 0.85   |
| Hallucination rate        | < 3%     |
| Refusal rate              | 5–10%    |
| Per-domain accuracy (min) | > 0.80   |
| Risk calibration (ECE)    | < 0.10   |
| Parking sign accuracy     | > 0.85   |
| Data freshness (alerts)   | < 60s    |
| Route planning latency    | < 500ms  |
| TTFT (streaming)          | < 800ms  |
| p95 latency (text)        | < 2s     |
| p95 latency (VLM)         | < 6s     |
| Text cost per query       | < $0.005 |
| VLM cost per query        | < $0.03  |
| Notification precision    | > 0.85   |
| Notification recall       | > 0.80   |
