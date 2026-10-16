# Pace

Pace tells you _when_ to leave and _how risky_ the trip is, not just how long it takes.

A conversational transit assistant for the Massachusetts Bay Transportation Authority (MBTA). Ask a question and get a grounded answer with sources, a recommended departure time, and a refusal when the data isn't there. Over time, Pace learns your usual commute and pings you when something's about to disrupt it.

---

## What it does

### Route quality

- **Departure-time recommendations** factoring in deadlines, current alerts, weather, and historical line reliability at that hour.
- **Calibrated risk labels** (low/mid/high) on every routing answer, measured by Expected Calibration Error.
- **Pre-computed backup routes** for common origin-destination pairs, so an alternate is ready when the primary breaks.
- **Fare, accessibility, and live Bluebikes availability** surfaced inside every routing answer.
- **Multi-stop planning** for chained trips.

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
