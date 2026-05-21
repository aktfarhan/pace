# prompts/

Every system prompt and few-shot example lives here.

---

## Files

| File                | Purpose                                                |
| ------------------- | ------------------------------------------------------ |
| `intent.md`         | intent classifier prompt                               |
| `generate.md`       | answer generation, citation-only enforcement           |
| `vlm_sign.md`       | parking sign VLM prompt + few-shot examples            |
| `refusal.md`        | templates for off-topic and low-confidence refusals    |
| `guard.md`          | confidence gate phrasing                               |

---

## Versioning

Every file starts with a YAML header:

```
version: 7
hash: a3f2b9
last_updated: 2026-05-20
notes: tightened the no-hallucination clause after refusal rate spiked
```

Every eval run records the prompt versions used.

---

## Rules

- Temperature 0 everywhere
- Citation-only: every claim in the output must trace to a retrieved chunk
- Refusal language is explicit ("the available sources don't cover that"), not hedged ("maybe try...")
- Voice rules apply — prompts must not contradict the persona
- No first-person ("I think...", "I recommend...") in any prompt output

---

## Editing flow

1. Edit the prompt file
2. Bump `version` and update `hash` to the new short git hash
3. Run `python -m eval.run --suite all` and confirm metrics held or improved
4. If a regression: revert, do not ship the change
5. Commit prompt + new eval run together — they're a pair
