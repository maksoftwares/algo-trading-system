# Independent EA Search Round 31

Generated: 2026-05-30

## Starting Point

Round 30 rejected the narrow GLD ETF flow-stress timing variant. Round 31 moved to a different GLD-related mechanism: relative safe-haven preference versus broad equities.

## Selected Lane

`h1_gld_spy_safe_haven_rotation_followthrough_v0`

Core idea:

```text
Use shifted 5-day GLD/SPY relative strength as a daily safe-haven preference proxy, then trade XAU H1 followthrough only when local XAU trend confirmation agrees.
```

Why this is process-safe:

- It is a fresh versioned v0 hypothesis.
- It is independent of the breakout-retest / level-and-pullback family.
- It reuses existing local GLD and SPY public ETF reference data.
- It was SHA256-locked before its result-producing matrix run.
- It stays in the research registry only and does not alter MT5 runtime, demo observers, or trade permissions.

## Machine Checks

Hypothesis file:

```text
docs/hypothesis_h1_gld_spy_safe_haven_rotation_followthrough_v0.md
```

Research hash:

```text
11a3e33af916b5632ce9570fa9baab769ec2187d97d7663a53575aedf847a021
```

Synthetic smoke:

```text
PASS - 2 synthetic signals, market trade plan generated, active registry disabled.
```

Real 9-cell matrix:

```text
REJECTED_FIRST_PASS - 1,596 total cost-cell trades, 9/9 trade-count cells, max zero-trade months 1, but 0/9 PF cells reached 1.30.
```

First-pass report:

```text
docs/H1_GLD_SPY_SAFE_HAVEN_ROTATION_FOLLOWTHROUGH_V0_FIRST_PASS.md
```

## Process Boundary

Do not tune this candidate in place after first-pass results. It showed broad but weak positive drift, not a buildable edge.

This lane does not alter active Phase 1/Phase 3 observation, Phase 2 readiness, approved expert status, dry-run permission, demo observer authority, or trade permissions.
