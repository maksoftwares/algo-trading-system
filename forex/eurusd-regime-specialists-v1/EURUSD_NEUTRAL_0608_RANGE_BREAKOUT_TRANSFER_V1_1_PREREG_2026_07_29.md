# EURUSD Neutral 06:00-08:00 UTC range-breakout transfer v1.1 preregistration

Status: `FROZEN_BEFORE_V1_1_CENSUS_AND_BEFORE_ANY_OUTCOME`

## Why v1.1 exists

V1 was frozen and pushed before its first EURUSD count. It produced 290
risk-eligible candidates and passed seven of eight capacity gates, but failed
because 18 candidates used regime states older than the frozen four-hour
maximum.

The v1 census loaded no post-entry path, exit, return, P&L, or oracle row.
Timestamp-only diagnosis showed that excluding those stale candidates would
leave adequate capacity. V1.1 is therefore capacity-aware but remains strictly
outcome-blind.

## The only revision

For every parent candidate:

```text
state_fresh = state_known_lag_hours <= 4.0
v1_1_risk_eligible = v1_risk_eligible AND state_fresh
```

Four hours is not a newly selected threshold. It is the exact maximum frozen
in the v1 preregistration before the first EURUSD candidate count.

## Everything else remains frozen

- The transferred USDJPY mechanism and all EURUSD signal parameters.
- The 06:00-08:00 UTC range and 08:00-12:00 UTC M15 breakout window.
- Current Neutral ownership and all non-freshness regime conditions.
- Entry, retail cost, stop, 1.5R target, 12-hour hold, and concurrency rules.
- All chronological capacity and performance gates.
- The evaluation-only Neutral oracle comparison.

## Stage boundary

The v1.1 census may load only completed decision-time inputs and timestamps.
It may not load any stop/target path, exit, return, P&L, or oracle row.

If every capacity gate passes, execution still remains prohibited until a
separate implementation and result contract are hash-locked, committed, and
pushed. A capacity pass alone is not evidence of profitability and cannot
authorize broker, demo, or live action.
