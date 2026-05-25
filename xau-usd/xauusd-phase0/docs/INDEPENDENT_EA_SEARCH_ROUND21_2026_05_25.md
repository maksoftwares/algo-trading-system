# Independent EA Search Round 21

Generated: 2026-05-25

## Starting Point

Round 20 rejected the breakeven-inflation lane. The next defensible step was a separate public macro family: nominal Treasury-rate and curve-shape stress.

## Selected Lane

`h4_treasury_curve_stress_momentum_v0`

Core idea:

```text
Trade H4 XAUUSD continuation only when shifted daily 2-year/10-year Treasury yield momentum and 10Y-2Y curve-spread movement confirm an easing/steepening or tightening/flattening state, then H4 price momentum confirms direction.
```

Why this is independent:

- It uses FRED `DGS2`, `DGS10`, and `T10Y2Y`, not broker OHLC geometry alone.
- It is not a retest, sweep, session, VWAP, XAG lead-lag, FX proxy, real-yield/dollar proxy, breakeven-inflation, COT positioning, GVZ, VIX, financial-conditions, or learned-state candidate.
- It directly tests a new information class: nominal Treasury-rate and yield-curve stress.

## Data Acquisition

Public FRED `DGS2`, `DGS10`, and `T10Y2Y` data were acquired into the local ignored raw-data directory:

```text
data/raw/treasury_curve/FRED_DGS2.csv
data/raw/treasury_curve/FRED_DGS10.csv
data/raw/treasury_curve/FRED_T10Y2Y.csv
```

The strategy shifts daily Treasury features by one observation before merging them into H4 bars, so H4 decisions do not use same-day Treasury observations.

## Machine Checks

Hypothesis file:

```text
docs/hypothesis_h4_treasury_curve_stress_momentum_v0.md
```

Synthetic smoke:

```text
PASS - 20 synthetic signals, market trade plans generated, active registry disabled.
```

Real 9-cell matrix:

```text
REJECTED_FIRST_PASS - 55 to 207 trades per cell, 3/9 PF cells reached 1.30, sample size/catastrophic-loss/cost sensitivity passed, but all passing cells were Pepperstone-only and concentration/activity failed.
```

First-pass report:

```text
docs/H4_TREASURY_CURVE_STRESS_MOMENTUM_V0_FIRST_PASS.md
```

## Process Boundary

Do not tune this candidate in place after first-pass results. Any future Treasury curve revisit needs a new versioned hypothesis and fresh SHA256 lock.

This lane does not alter active Phase 1 soak, Phase 2 readiness, approved expert status, dry-run permission, or trade permissions.
