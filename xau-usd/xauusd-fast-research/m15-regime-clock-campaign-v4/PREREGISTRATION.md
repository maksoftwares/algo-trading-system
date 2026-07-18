# XAUUSD M15 Regime Clock Campaign V4 Preregistration

## Purpose

The fixed-rule M15 target and anti-signal campaigns found no robust chop or
transition specialist. Earlier calendar strategies were not conditioned on the
causal H4 regime. This changed approach tests whether a completed-session or
clock effect exists only while H4 is classified as `CHOP` or
`TRANSITION_UNKNOWN`.

## Frozen Search

Attempts 20,120 through 21,119 contain exactly 1,000 deterministic definitions:
100 variants for each of five chop and five transition mechanics. Variant
selection from each declared Cartesian parameter space is deterministic and
outcome-blind. The mechanics are fixed clock carry, Asian inventory response,
prior-day response, completed-session handoff, and ancestry-aware clock response.

The campaign does not alter the H4 regime classifier. `UNSAFE_SHOCK` is never
eligible. A transition signal may use only the last resolved regime and the age
of the active transition known at the completed M15 decision.

## Causality And Execution

- Asian inventory uses the 05:45-06:00 UTC M15 close and is unavailable before
  06:00 UTC.
- Prior-day return is shifted by one complete UTC day.
- Local session returns use completed M15 bars only.
- Entry is the next M15 executable Ask for long or Bid for short.
- Stops and targets execute on the opposite quote, with stop-first ambiguity,
  native spread, ticket cost, holding cost, and stress slippage.
- One definition may hold one position at a time and take at most six trades per
  UTC day.

## Frozen Gates

The inherited gates require at least 120 trades overall, 15 in each of four
eras, stressed PF at least 1.10 and average stressed R at least 0.02 in every
era, total PF at least 1.25, drawdown no more than 30R, and positive net R after
removing the five largest winners. Benjamini-Hochberg q-values are reported
across all 1,000 definitions at 10% FDR.

All historical periods are discovery evidence because earlier research has
already inspected them. Any economic finalist still requires separate raw-tick
confirmation and prospective shadow observation. This package grants no model
training, Python serving, EA, demo, live, broker, Databento, or paid-data
authority.
