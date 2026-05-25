# Independent EA Search Round 16

Generated: 2026-05-25

## Starting Point

Round 15 fixed the real-yield macro blocker and rejected the FRED macro lane. The next defensible step was a different external data class rather than another XAU-only setup.

## Selected Lane

`cot_gold_positioning_reversal_v0`

Core idea:

```text
Trade H4 XAUUSD reversals only when official weekly CFTC gold futures positioning shows managed-money crowding against producer/merchant positioning, then H4 price confirms the turn.
```

Why this is independent:

- It uses official CFTC COT positioning data, not broker OHLC geometry.
- It is not a retest, sweep, session, VWAP, volatility-squeeze, XAG lead-lag, real-yield macro, or learned-state candidate.
- It directly tests a new information class: futures market participant positioning.

## Data Acquisition

Official CFTC historical compressed disaggregated futures-only annual files were acquired for 2016-2024. The gold contract rows were compressed into:

```text
data/reference/cot/gold_disaggregated_futures_only_2016_2024.csv
```

The strategy treats each Tuesday COT report as usable only from the following Monday 00:00 UTC.

## Machine Checks

Hypothesis file:

```text
docs/hypothesis_cot_gold_positioning_reversal_v0.md
```

Synthetic smoke:

```text
PASS - 3 synthetic signals, market trade plan generated, active registry disabled.
```

Real 9-cell matrix:

```text
REJECTED_FIRST_PASS - 5 to 24 trades per cell, 0/9 PF cells reached 1.30, and sample-size/concentration/activity failed in every cell.
```

First-pass report:

```text
docs/COT_GOLD_POSITIONING_REVERSAL_V0_FIRST_PASS.md
```

## Process Boundary

Do not tune this candidate in place after first-pass results. Any future COT revisit needs a new versioned hypothesis and fresh SHA256 lock.

This lane does not alter active Phase 1 soak, Phase 2 readiness, approved expert status, dry-run permission, or trade permissions.
