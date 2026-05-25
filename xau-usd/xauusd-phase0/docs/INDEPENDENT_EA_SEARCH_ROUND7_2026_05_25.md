# Independent EA Search Round 7

Generated: 2026-05-25

## Starting Point

Round 6 tested the first deterministic AI-style learned state, fixed a neutral tick-count blocker, and still rejected the candidate because 0 of 9 matrix cells reached PF 1.30.

## Selected Lane

`h1_calendar_drift_state_v0`

Core idea:

```text
Learn whether the same UTC hour-of-week has produced repeatable ATR-normalized 6-hour forward drift, then trade only when the locked same-bucket evidence threshold is met.
```

Why this is independent:

- It uses calendar/time-of-week behavior, not levels, retests, sweeps, VWAP, volume, intermarket proxies, or multi-feature price models.
- It is learned walk-forward but each score is explainable from prior same-bucket observations.
- It needs no new data and can be falsified under the existing 9-cell matrix.

## Required Data

No new data is required. The candidate uses existing XAUUSD H1 feature bars and M5 execution bars across the standard 9-cell matrix.

## Machine Checks

Hypothesis file:

```text
docs/hypothesis_h1_calendar_drift_state_v0.md
```

Research boundary:

```text
Research-only candidate. It must be run through explicit research commands and must not enter the active `all` expert set.
```

Synthetic smoke:

```text
PASS - 45 synthetic signals, market trade plan generated, active registry disabled.
```

Real 9-cell matrix:

```text
REJECTED_FIRST_PASS - 802 to 1209 trades per cell, but 0/9 PF cells reached 1.30 and catastrophic loss failed in Capital.com and Dukascopy windows.
```

First-pass report:

```text
docs/H1_CALENDAR_DRIFT_STATE_V0_FIRST_PASS.md
```

## Process Boundary

Do not tune this candidate in place after first-pass results. Any future revisit needs a new versioned hypothesis and fresh SHA256 lock.

This lane does not alter active Phase 1 soak, Phase 2 readiness, approved expert status, dry-run permission, or trade permissions.
