---
version: 3
hash: '39042b7'
last_updated: 2026-10-16
notes: parking removed; new off-topic text, and the parking-only outside-coverage refusal is gone
---

Refusal templates the system uses when it won't answer. Each one has a key, a trigger, and the exact text shown to the user.

Priority when more than one fits: adversarial > off-topic > low-confidence.

## off-topic

- **Key:** `off-topic`
- **Trigger:** Intent classifier returns `off-topic`.
- **Placeholders:** none.
- **Template:**

```
Pace covers MBTA transit. That falls outside the scope.
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

## outside-service-area

- **Key:** `outside-service-area`
- **Trigger:** Transit query whose origin or destination falls outside the MBTA service area.
- **Placeholders:** none.
- **Template:**

```
Pace only covers the MBTA service area.
```
