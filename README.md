# Pace

Pace tells you _when_ to leave and _how risky_ the trip is, not just how long it takes.

A conversational transit assistant for the Massachusetts Bay Transportation Authority (MBTA). Ask a question and get a grounded answer with sources, a recommended departure time, and a refusal when the data isn't there. Snap a photo of a parking sign and Pace tells you if you can park there right now. Over time, Pace learns your usual commute and pings you when something's about to disrupt it.

---

## What it does

### Route quality

- **Departure-time recommendations** factoring in deadlines, current alerts, weather, and historical line reliability at that hour.
- **Calibrated risk labels** (low/mid/high) on every routing answer, measured by Expected Calibration Error.
- **Pre-computed backup routes** for common origin-destination pairs, so an alternate is ready when the primary breaks.
- **Fare, accessibility, and live Bluebikes availability** surfaced inside every routing answer.
- **Multi-stop planning** for chained trips.

### Parking

- **Parking sign photo reader** for Boston and Cambridge — answers in the current context, including which city's rules apply.
- **Permit zone check** — confirms your spot is in the zone the sign requires.

### Behavior

- **Citation-only answers** with refusal when the data is insufficient.
- **Learned routines** with proactive push notifications when a disruption hits a confirmed commute.

---

## What an answer looks like

> **Q:** How do I get from Central to South Station? Need to be there by 10am.
>
> **Pace:**
>
> - **Leave at 8:42** to make 10am
> - Red Line south, 14 min, $2.40
> - Signal issue at Park — southbound +12 min
> - Backup: Bus 47 (+7 min on average)
>
> _Risk: mid · Sources: [MBTA alert RL-2026-05-17](#), [Schedule](#)_

> **Q:** _(Photo of a Cambridge street sign reading "VISITOR PERMIT ZONE 4 ONLY — 4PM-10PM")_ Can I park here?
>
> **Pace:**
>
> - **Yes** — it's 2:15 PM and the restriction starts at 4 PM
> - You're standing in Zone 4 right now
> - After 4 PM, this spot requires a Visitor Permit Zone 4 pass
>
> _Sources: [Cambridge Title 10 §10.18](#), [Visitor Permit Boundaries](#)_

---

## Progress

Thirteen weeks across four phases.

- [ ] Week 1 — Scope locked, eval set seeded, copy and ADRs committed
- [ ] Week 2 — Data pipelines (MBTA + boston.gov + Cambridge), with accessibility, fare, and permit-zone metadata
- [ ] Week 3 — Remaining data + hybrid retrieval + eval harness
- [ ] Week 4 — End-to-end Q&A with fare, accessibility, bike, last-train surfaces
- [ ] Week 5 — Delay-prediction model trained and calibrated
- [ ] Week 6 — Route planner backend (multi-modal, multi-stop, future-time) + counterfactuals
- [ ] Week 7 — Parking sign VLM + sign eval set
- [ ] Week 8 — Frontend chat + map + onboarding + settings + history + multi-stop + calendar export
- [ ] Week 9 — Personal memory + saved places + "what Pace knows" page + data delete
- [ ] Week 10 — Notifications + PWA install + permission flow + routine confirmation
- [ ] Week 11 — Buffer and polish
- [ ] Week 12 — Deploy and soft launch
- [ ] Week 13 — Case study and wrap-up
