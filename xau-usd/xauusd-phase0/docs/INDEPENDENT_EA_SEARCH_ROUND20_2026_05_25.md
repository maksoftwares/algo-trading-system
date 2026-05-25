# Independent EA Search Round 20

Generated: 2026-05-25

## Starting Point

Round 19 rejected the broad financial-conditions lane. The next defensible step was another macro input family that is separate from spot-gold structure, XAG/FX proxies, real-yield/dollar state, COT positioning, GVZ, VIX, and NFCI/ANFCI.

## Selected Lane

`h4_breakeven_inflation_momentum_v0`

Core idea:

```text
Trade H4 XAUUSD continuation only when shifted daily 5-year and 10-year breakeven inflation momentum confirms an inflation or disinflation state, then H4 price momentum confirms direction.
```

Why this is independent:

- It uses FRED `T5YIE` and `T10YIE` market-implied inflation-expectations data, not broker OHLC geometry alone.
- It is not a retest, sweep, session, VWAP, XAG lead-lag, FX proxy, real-yield macro, COT positioning, GVZ, VIX, financial-conditions, or learned-state candidate.
- It directly tests a new information class: Treasury/TIPS-implied inflation compensation.

## Data Acquisition

Public FRED `T5YIE` and `T10YIE` data were acquired into the local ignored raw-data directory:

```text
data/raw/inflation_expectations/FRED_T5YIE.csv
data/raw/inflation_expectations/FRED_T10YIE.csv
```

The strategy shifts daily breakeven features by one observation before merging them into H4 bars, so H4 decisions do not use same-day breakeven observations.

## Machine Checks

Hypothesis file:

```text
docs/hypothesis_h4_breakeven_inflation_momentum_v0.md
```

Synthetic smoke:

```text
PASS - 20 synthetic signals, market trade plans generated, active registry disabled.
```

Real 9-cell matrix:

```text
REJECTED_FIRST_PASS - 183 to 273 trades per cell, 0/9 PF cells reached 1.30, sample size/activity/cost sensitivity passed, and concentration failed in seven cells.
```

First-pass report:

```text
docs/H4_BREAKEVEN_INFLATION_MOMENTUM_V0_FIRST_PASS.md
```

## Process Boundary

Do not tune this candidate in place after first-pass results. Any future inflation-expectations revisit needs a new versioned hypothesis and fresh SHA256 lock.

This lane does not alter active Phase 1 soak, Phase 2 readiness, approved expert status, dry-run permission, or trade permissions.
