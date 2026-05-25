# Independent EA Search Round 18

Generated: 2026-05-25

## Starting Point

Round 17 rejected the GVZ gold-options implied-volatility lane. The next defensible step was another external data class rather than tuning the rejected GVZ v0 thresholds.

## Selected Lane

`h4_vix_risk_off_reversal_v0`

Core idea:

```text
Trade H4 XAUUSD reversals only when shifted daily VIX state shows equity-risk stress or risk-relief, then H4 price confirms a reversal candle after a two-day directional move.
```

Why this is independent:

- It uses VIX equity-options implied volatility, not broker OHLC geometry alone.
- It is not a retest, sweep, session, VWAP, XAG lead-lag, FX proxy, real-yield macro, COT positioning, gold-options GVZ, or learned-state candidate.
- It directly tests a new information class: cross-asset equity-risk implied volatility.

## Data Acquisition

Public FRED `VIXCLS` data was acquired into the local ignored raw-data directory:

```text
data/raw/risk/FRED_VIXCLS.csv
```

The strategy shifts VIX daily-close features by one observation before merging them into H4 bars, so H4 decisions do not see same-day VIX close values.

## Machine Checks

Hypothesis file:

```text
docs/hypothesis_h4_vix_risk_off_reversal_v0.md
```

Synthetic smoke:

```text
PASS - 1 synthetic signal, market trade plan generated, active registry disabled.
```

Real 9-cell matrix:

```text
REJECTED_FIRST_PASS - 47 to 61 trades per cell, 3/9 PF cells reached 1.30, sample size passed, and concentration failed in every cell.
```

First-pass report:

```text
docs/H4_VIX_RISK_OFF_REVERSAL_V0_FIRST_PASS.md
```

## Process Boundary

Do not tune this candidate in place after first-pass results. Any future VIX/risk-off revisit needs a new versioned hypothesis and fresh SHA256 lock.

This lane does not alter active Phase 1 soak, Phase 2 readiness, approved expert status, dry-run permission, or trade permissions.
