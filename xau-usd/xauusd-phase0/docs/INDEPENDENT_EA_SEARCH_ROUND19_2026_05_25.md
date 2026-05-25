# Independent EA Search Round 19

Generated: 2026-05-25

## Starting Point

Round 18 rejected the VIX equity-risk implied-volatility lane. The next defensible step was another broad external risk-state data class rather than tuning the rejected VIX v0 thresholds.

## Selected Lane

`h4_financial_conditions_stress_reversal_v0`

Core idea:

```text
Trade H4 XAUUSD reversals only when shifted weekly Chicago Fed financial-conditions data shows tightening/stress or easing/relief, then H4 price confirms a reversal candle after a two-day directional move.
```

Why this is independent:

- It uses NFCI/ANFCI financial-conditions data, not broker OHLC geometry alone.
- It is not a retest, sweep, session, VWAP, XAG lead-lag, FX proxy, real-yield macro, COT positioning, GVZ, VIX, or learned-state candidate.
- It directly tests a new information class: broad weekly U.S. financial conditions.

## Data Acquisition

Public FRED `NFCI` and `ANFCI` data were acquired into the local ignored raw-data directory:

```text
data/raw/financial_conditions/FRED_NFCI.csv
data/raw/financial_conditions/FRED_ANFCI.csv
```

The strategy shifts weekly financial-conditions features by one observation before merging them into H4 bars, so H4 decisions do not see same-week values before publication.

## Machine Checks

Hypothesis file:

```text
docs/hypothesis_h4_financial_conditions_stress_reversal_v0.md
```

Synthetic smoke:

```text
PASS - 1 synthetic signal, market trade plan generated, active registry disabled.
```

Real 9-cell matrix:

```text
REJECTED_FIRST_PASS - 46 to 61 trades per cell, 0/9 PF cells reached 1.30, sample size passed, and concentration/activity failed in every cell.
```

First-pass report:

```text
docs/H4_FINANCIAL_CONDITIONS_STRESS_REVERSAL_V0_FIRST_PASS.md
```

## Process Boundary

Do not tune this candidate in place after first-pass results. Any future financial-conditions revisit needs a new versioned hypothesis and fresh SHA256 lock.

This lane does not alter active Phase 1 soak, Phase 2 readiness, approved expert status, dry-run permission, or trade permissions.
