# Independent EA Search Round 30

Generated: 2026-05-30

## Starting Point

Round 29 rejected `h1_month_turn_flow_reversion_v0`. Round 30 returned to the strongest independent PF lead found so far: GLD ETF flow-stress reversal.

## Selected Lane

`h4_gld_etf_flow_reversal_v2`

Core idea:

```text
Preserve the strict v0 GLD ETF participation-stress thresholds, but allow the 08:00 UTC H4 decision bar in addition to 12:00, 16:00, and 20:00 UTC.
```

Why this is process-safe:

- It is a new versioned hypothesis, not an edit to the rejected v0/v1 files.
- It is explicitly result-informed and documented as such.
- It changes only timing coverage, not the GLD stress thresholds, stop, target, or time stop.
- It remains independent of the breakout-retest / level-and-pullback family.
- It stays in the research registry only and does not alter MT5 runtime, demo observers, or trade permissions.

## Machine Checks

Hypothesis file:

```text
docs/hypothesis_h4_gld_etf_flow_reversal_v2.md
```

Research hash:

```text
4920e7f4a9928186d6bfc4306518d0b311fdadc7126dadd11469152d1e276821
```

Synthetic smoke:

```text
PASS - 1 synthetic signal, market trade plan generated, active registry disabled.
```

Real 9-cell matrix:

```text
REJECTED_FIRST_PASS - 378 total cost-cell trades, 6/9 PF cells, 6/9 trade-count cells, max zero-trade months 5, and concentration failure.
```

First-pass report:

```text
docs/H4_GLD_ETF_FLOW_REVERSAL_V2_FIRST_PASS.md
```

## Process Boundary

Do not tune this candidate in place after first-pass results. This lane remains the strongest independent PF clue, but it is still not a selected EA because activity and concentration remain insufficient.

This lane does not alter active Phase 1/Phase 3 observation, Phase 2 readiness, approved expert status, dry-run permission, demo observer authority, or trade permissions.
