# Independent EA Search Round 22

Generated: 2026-05-25

## Starting Point

Round 21 rejected the nominal Treasury-rate and yield-curve lane. The next defensible step was a narrower credit-stress family rather than tuning the rejected Treasury thresholds.

## Selected Lane

`h4_credit_spread_stress_momentum_v0`

Core idea:

```text
Trade H4 XAUUSD continuation only when shifted daily Baa/Aaa corporate credit-spread stress confirms a credit-risk state, then H4 price momentum confirms direction.
```

Why this is independent:

- It uses FRED `BAA10Y` and `AAA10Y`, not broker OHLC geometry alone.
- It is not a retest, sweep, session, VWAP, XAG lead-lag, FX proxy, real-yield/dollar proxy, breakeven-inflation, Treasury curve, COT positioning, GVZ, VIX, financial-conditions, or learned-state candidate.
- It directly tests a new information class: corporate credit spread stress.

## Data Acquisition

Public FRED `BAA10Y` and `AAA10Y` data were acquired into the local ignored raw-data directory:

```text
data/raw/credit_spread/FRED_BAA10Y.csv
data/raw/credit_spread/FRED_AAA10Y.csv
```

The ICE high-yield OAS family was checked first, but the accessible FRED CSV returned only a recent post-2023 slice or HTML for nearby series, so it was not suitable for Phase 0 matrix coverage. Moody's Baa/Aaa spread series covered the matrix windows and was used instead.

## Machine Checks

Hypothesis file:

```text
docs/hypothesis_h4_credit_spread_stress_momentum_v0.md
```

Synthetic smoke:

```text
PASS - 20 synthetic signals, market trade plans generated, active registry disabled.
```

Real 9-cell matrix:

```text
REJECTED_FIRST_PASS - 153 to 211 trades per cell, 0/9 PF cells reached 1.30, sample size/catastrophic-loss/cost sensitivity passed, but concentration failed in every cell and activity failed in six cells.
```

First-pass report:

```text
docs/H4_CREDIT_SPREAD_STRESS_MOMENTUM_V0_FIRST_PASS.md
```

## Process Boundary

Do not tune this candidate in place after first-pass results. Any future credit-spread revisit needs a new versioned hypothesis and fresh SHA256 lock.

This lane does not alter active Phase 1 soak, Phase 2 readiness, approved expert status, dry-run permission, or trade permissions.
