---
version: 1
hash: '1e10010'
last_updated: 2026-05-21
notes: initial draft
---

Refusal templates the system uses when it won't answer. Each one has a key, a trigger, and the exact text shown to the user.

Priority when more than one fits: adversarial > outside-coverage > off-topic > low-confidence.

## off-topic

- **Key:** `off-topic`
- **Trigger:** Intent classifier returns `off-topic`.
- **Placeholders:** none.
- **Template:**

```
Pace covers MBTA transit and Boston/Cambridge parking. That falls outside the scope.
```

## low-confidence

- **Key:** `low-confidence`
- **Trigger:** No retrieved chunk passes the threshold, or the gate returns `REFUSE:low-confidence`.
- **Placeholders:** `{source_link}` (optional)
- **Template (with link):**

```
The available sources don't cover that with enough certainty. For an authoritative answer, try {source_link}.
```

- **Fallback (no link):**

```
The available sources don't cover that with enough certainty.
```

## adversarial

- **Key:** `adversarial`
- **Trigger:** Prompt injection, slurs, unsafe requests, or otherwise unprocessable input. Fires first if multiple triggers match.
- **Placeholders:** none.
- **Template:**

```
That question can't be processed as written. Rephrase or ask something else.
```

## outside-coverage

- **Key:** `outside-coverage`
- **Trigger:** Parking-rules query for a city other than Boston or Cambridge.
- **Placeholders:** `{city}` (required)
- **Template:**

```
Pace covers Boston and Cambridge for parking rules. Transit answers extend to the rest of the MBTA service area. For {city}, try the local agency.
```
