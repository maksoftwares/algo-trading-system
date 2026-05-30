# Independent EA Search Round 29

Generated: 2026-05-30

## Starting Point

Round 28 tested H1 tick-volume climax continuation and rejected it first-pass. Round 29 moved back to calendar-flow behavior to test the opposite side of the already-rejected month-turn continuation thesis.

## Selected Lane

`h1_month_turn_flow_reversion_v0`

Core idea:

```text
Use month-end / month-start H1 pressure extensions in XAU as an unwind candidate, entering against the prior 6h/24h move when the bar closes stretched from EMA21 but not catastrophically far from EMA50.
```

Why this is process-safe:

- It is a new versioned calendar-flow hypothesis, not a tuned version of the rejected continuation candidate.
- It is mechanically distinct from the level/retest approved family.
- It was SHA256-locked before its result-producing matrix run.
- It stays in the research registry only and does not alter MT5 runtime, demo observers, or trade permissions.

## Machine Checks

Hypothesis file:

```text
docs/hypothesis_h1_month_turn_flow_reversion_v0.md
```

Synthetic smoke:

```text
PASS - 1 synthetic signal, market trade plan generated, active registry disabled.
```

Real 9-cell matrix:

```text
REJECTED_FIRST_PASS - 780 total cost-cell trades, 9/9 trade-count cells, 0/9 PF cells reached 1.30. Dukascopy was positive below threshold; Capital.com and Pepperstone were negative or near flat.
```

First-pass report:

```text
docs/H1_MONTH_TURN_FLOW_REVERSION_V0_FIRST_PASS.md
```

## Process Boundary

Do not tune this candidate in place after first-pass results. Any future month-turn/calendar-flow revisit needs a new versioned hypothesis with a materially different mechanism.

This lane does not alter active Phase 1/Phase 3 observation, Phase 2 readiness, approved expert status, dry-run permission, demo observer authority, or trade permissions.
