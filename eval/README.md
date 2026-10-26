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

| Field             | Values                                                      |
| ----------------- | ----------------------------------------------------------- |
| `id`              | unique string                                               |
| `query`           | the user-facing question                                    |
| `domain`          | `route` \| `alert` \| `schedule` \| `info` \| `off-topic`   |
| `style`           | `formal` \| `casual` \| `typo` \| `abbrev` \| `adversarial` |
| `gold_answer`     | reference answer for LLM-as-judge scoring                   |
| `gold_sources`    | canonical sources that should appear in citations           |
| `expected_action` | `answer` \| `refuse` \| `clarify`                           |
| `expected_risk`   | `low` \| `mid` \| `high` \| `n/a`                           |
| `notes`           | author commentary                                           |

---

## Distribution policy

| Domain    | Share |
| --------- | ----- |
| route     | 38%   |
| alert     | 19%   |
| schedule  | 21%   |
| info      | 10%   |
| off-topic | 12%   |

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
  "notes": "2026-07-10: ranked below 20; Lynn 426 and suburban Central St stops won"
}
```

Fields:

| Field      | Values                                              |
| ---------- | --------------------------------------------------- |
| `id`       | unique string                                       |
| `query`    | the user-facing question                            |
| `expected` | chunk ids that answer the query; hit if any returns |
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
| `problem`  | optional: `unclear`, `outside` or `missing`           |

`expected` holds root ids, with the alias index dropped. Addresses and streets have no id, so their label is the key. Every id naming the same physical point is listed.

A row with `problem` needs the search to say why it found no one place: `unclear` when two towns are about as near (then `expected` lists the guesses), `outside` when the town named has no such address but other towns do, and `missing` when nothing like it exists.

Rows with an empty `expected` are scored on their own line, so a change that widens matching cannot hide inside the headline count.

Run with `python -m eval.run_places`. Re-run after any change to ranking, normalization, or the places data.

---

## Parse set

Each line in `parse.jsonl` is one question and what the question reader model should read from it.

```
{
  "id": "x-0001",
  "query": "harvard to back bay nov 16 at 7pm",
  "intent": "route",
  "origin": "harvard",
  "destination": "back bay",
  "day": "2026-11-16",
  "leave_at": "7:00 PM",
  "stations": ["place-harsq", "place-bbsta"],
  "notes": "a written date with a leave time"
}
```

Fields:

| Field                  | Values                                                                |
| ---------------------- | --------------------------------------------------------------------- |
| `id`                   | the seed id for seed questions, `x-`, `b-`, `h-` or `f-` for the rest |
| `query`                | the user-facing question                                              |
| `intent`               | a domain                                                              |
| `hard`                 | true when turning the question down as off-topic also counts as right |
| `origin` ... `headway` | the read fields; a missing field means empty                          |
| `stations`             | station ids the origin and destination point to                       |
| `notes`                | author commentary                                                     |

Every row is read as if asked on Wednesday, November 4, 2026 at 8:30 AM, so "tomorrow" and "nov 2" always mean the same date. Rows marked `off-topic` are scored on intent alone.

Run with `python -m eval.run_parse`. Re-run after any change to `backend/assistant/parse.py` or `backend/mbta/stations.py`.

---

## Answer set

`run_answers.py` runs every query in `seed.jsonl` through the full pipeline and checks: answered when it should answer, refused when it should refuse.

Expected action comes from `expected_action`.

Run with `python -m eval.run_answers`. Re-run after any prompt change.

---

## Splits

- `seed.jsonl` — dev set, tune freely
- `retrieval.jsonl` — retrieval checks, re-run after any retrieval change
- `places.jsonl` — destination resolution, re-run after any ranking or places-data change
- `parse.jsonl` — the question reader, re-run after any parser, training or station change
- `parse_holdout.jsonl` — the question reader's final-number set
- `holdout.jsonl` — final-number set, never tuned against

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
| Data freshness (alerts)   | < 60s    |
| Route planning latency    | < 500ms  |
| TTFT (streaming)          | < 800ms  |
| p95 latency (text)        | < 2s     |
| Text cost per query       | < $0.005 |
| Notification precision    | > 0.85   |
| Notification recall       | > 0.80   |
