# Independent EA Search Round 27

Generated: 2026-05-30

## Starting Point

The prior CYB/UUP yuan-dollar FX rotation lane was blocked because public Yahoo CYB ETF coverage ended on 2023-10-30, short of the required matrix window. Round 27 tested the same macro family with an official FRED CNY-dollar input instead of the stale ETF proxy.

## Selected Lane

`h1_cny_dollar_pressure_followthrough_v0`

Core idea:

```text
Use shifted official FRED DEXCHUS yuan-per-dollar data plus broad-dollar pressure to trade XAU H1 follow-through only when CNY-dollar pressure and local XAU momentum agree.
```

Why this is process-safe:

- It uses a new official-data input class rather than partial CYB/UUP ETF coverage.
- It has a new name, new hypothesis, and fresh SHA256 lock before matrix review.
- It stays in the research registry only and does not alter Phase 1/Phase 2/Phase 3 runtime.
- The pressure thresholds, XAU confirmation, stop, target, time stop, and duplicate-control rules are fixed in the hypothesis.

## Machine Checks

Hypothesis file:

```text
docs/hypothesis_h1_cny_dollar_pressure_followthrough_v0.md
```

Synthetic smoke:

```text
PASS - 2 synthetic signals, market trade plan generated, active registry disabled.
```

Real 9-cell matrix:

```text
REJECTED_FIRST_PASS - 1,188 total cost-cell trades, 9/9 trade-count cells, 0/9 PF cells reached 1.30. Capital.com/Pepperstone were positive below threshold; Dukascopy was negative.
```

First-pass report:

```text
docs/H1_CNY_DOLLAR_PRESSURE_FOLLOWTHROUGH_V0_FIRST_PASS.md
```

## Process Boundary

Do not tune this candidate in place after first-pass results. Any future yuan-dollar pressure revisit needs a new versioned hypothesis with a distinct mechanic and fresh SHA256 lock.

This lane does not alter active Phase 1 soak, Phase 2 readiness, approved expert status, dry-run permission, demo observer authority, or trade permissions.
