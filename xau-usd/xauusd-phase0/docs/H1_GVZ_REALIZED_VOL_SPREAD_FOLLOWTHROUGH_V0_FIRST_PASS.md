# H1 GVZ Realized-Volatility Spread Follow-Through v0 First Pass

Generated: 2026-05-30
Status: `REJECTED_FIRST_PASS`

## Decision

Reject `h1_gvz_realized_vol_spread_followthrough_v0` without tuning.

This candidate tested whether shifted GVZ implied-volatility premium versus H1 XAU realized volatility supports H1 continuation after local price has already aligned with the volatility-pressure state. It produced positive returns in all cells, but failed PF persistence with only 1/9 cells above 1.30 and failed activity in the Capital.com and Pepperstone windows.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero Months | Result |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | capital_com | best_case | 46 | 43.48% | 1.0822 | +1.05% | 3.70% | 12 | FAIL |
| 2 | capital_com | median | 46 | 43.48% | 1.0822 | +1.05% | 3.70% | 12 | FAIL |
| 3 | capital_com | p95 | 46 | 43.48% | 1.0574 | +0.74% | 3.75% | 12 | FAIL |
| 4 | pepperstone | best_case | 44 | 45.45% | 1.1705 | +1.95% | 2.74% | 11 | FAIL |
| 5 | pepperstone | median | 44 | 45.45% | 1.1705 | +1.95% | 2.74% | 11 | FAIL |
| 6 | pepperstone | p95 | 44 | 45.45% | 1.1595 | +1.82% | 2.75% | 11 | FAIL |
| 7 | dukascopy | best_case | 86 | 46.51% | 1.3142 | +6.89% | 4.46% | 4 | PASS_PF_ONLY |
| 8 | dukascopy | median | 86 | 46.51% | 1.2970 | +6.50% | 4.36% | 4 | FAIL |
| 9 | dukascopy | p95 | 86 | 46.51% | 1.2573 | +5.64% | 4.55% | 4 | FAIL |

## Gate Snapshot

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| PF cells >= 1.30 | 1/9 | >= 7/9 | FAIL |
| Trade-count cells >= 40 | 9/9 | 9/9 | PASS |
| Total matrix trades | 528 | Informational | PASS |
| Max zero-trade months | 12 | <= 3 | FAIL |
| Cross-broker persistence | Dukascopy-only PF-threshold pocket | Robust across windows | FAIL |
| Best observed PF | 1.3142 | >= 1.30 in most cells | FAIL |

## Interpretation

The paired GVZ-realized-volatility follow-through expression is a useful clue because all cells were positive, but it is too sparse and broker-dependent to approve. The only PF-threshold cell was Dukascopy best-case; median and P95 cost cases fell back below threshold.

## Next Action

Do not tune v0. Treat public daily GVZ implied-volatility premium as a weak lead only. A future options-volatility lane would need materially better data, such as gold options skew, term structure, or intraday options/futures volatility, before a new hypothesis is justified.
