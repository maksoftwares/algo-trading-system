# Independent EA Search Round 17

Generated: 2026-05-25

## Starting Point

Round 16 rejected the official CFTC COT futures-positioning lane. The next defensible step was another external data class rather than a threshold edit to a rejected v0.

## Selected Lane

`h4_gvz_volatility_panic_reversal_v0`

Core idea:

```text
Trade H4 XAUUSD panic reversals only when shifted daily GVZ implied-volatility state shows a high/rising gold-options stress regime, then H4 price confirms a reversal candle after a two-day directional move.
```

Why this is independent:

- It uses GVZ gold-options implied volatility, not broker OHLC geometry alone.
- It is not a retest, sweep, session, VWAP, XAG lead-lag, FX proxy, real-yield macro, COT positioning, or learned-state candidate.
- It directly tests a new information class: listed-options market-implied gold stress.

## Data Acquisition

Public FRED `GVZCLS` data was acquired into the local ignored raw-data directory:

```text
data/raw/options/FRED_GVZCLS.csv
```

The strategy shifts GVZ daily-close features by one observation before merging them into H4 bars, so H4 decisions do not see same-day GVZ close values.

## Machine Checks

Hypothesis file:

```text
docs/hypothesis_h4_gvz_volatility_panic_reversal_v0.md
```

Synthetic smoke:

```text
PASS - 1 synthetic signal, market trade plan generated, active registry disabled.
```

Real 9-cell matrix:

```text
REJECTED_FIRST_PASS - 48 to 60 trades per cell, 0/9 PF cells reached 1.30, sample size passed, and concentration/activity failed in every cell.
```

First-pass report:

```text
docs/H4_GVZ_VOLATILITY_PANIC_REVERSAL_V0_FIRST_PASS.md
```

## Process Boundary

Do not tune this candidate in place after first-pass results. Any future implied-volatility revisit needs a new versioned hypothesis and fresh SHA256 lock.

This lane does not alter active Phase 1 soak, Phase 2 readiness, approved expert status, dry-run permission, or trade permissions.
