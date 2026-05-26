# Independent EA Search Round 26

Generated: 2026-05-26

## Starting Point

Round 25 tested public policy-uncertainty state and failed with Pepperstone-only strength. A mechanically different H1 event-regime lane was selected to test whether scheduled macro timing adds information beyond slow macro levels and generic calendar drift.

## Selected Lane

`h1_macro_event_aftershock_v0`

Core idea:

```text
Use standardized high-impact US macro event slots as timing regimes, then trade the first H1 aftershock direction if the event move and event range exceed fixed ATR thresholds.
```

Why this is process-safe:

- It uses a new event-regime mechanism rather than tuning any rejected macro or H1 state candidate.
- It has a new name, new hypothesis, and new SHA256 lock before any smoke or matrix run.
- The event-slot rules, confirmation timing, thresholds, stop, target, and time stop are fixed in the hypothesis.

## Machine Checks

Hypothesis file:

```text
docs/hypothesis_h1_macro_event_aftershock_v0.md
```

Synthetic smoke:

```text
PASS - 1 synthetic signal, market trade plan generated, active registry disabled.
```

Real 9-cell matrix:

```text
REJECTED_FIRST_PASS - 85 to 93 trades per cell, 0/9 PF cells reached 1.30, sample size/activity/cost sensitivity passed, but concentration failed in every cell.
```

First-pass report:

```text
docs/H1_MACRO_EVENT_AFTERSHOCK_V0_FIRST_PASS.md
```

## Process Boundary

Do not tune this candidate in place after first-pass results. Any future event-regime revisit needs a new versioned hypothesis and fresh SHA256 lock.

This lane does not alter active Phase 1 soak, Phase 2 readiness, approved expert status, dry-run permission, or trade permissions.
