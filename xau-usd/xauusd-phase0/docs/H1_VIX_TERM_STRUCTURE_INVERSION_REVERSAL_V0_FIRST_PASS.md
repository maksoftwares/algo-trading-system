# H1 VIX Term-Structure Inversion Reversal v0 First Pass

Generated: 2026-05-30
Status: `REJECTED_FIRST_PASS`

## Decision

Reject `h1_vix_term_structure_inversion_reversal_v0` without tuning.

This candidate produced enough trades in all 9 cells, but no cell reached PF >= 1.30. Capital.com was materially negative, while Pepperstone and Dukascopy were mildly positive below threshold. Dukascopy also exceeded the max zero-trade-month gate and concentration failed.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero Months | Result |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | capital_com | best_case | 70 | 30.00% | 0.5681 | -9.40% | 10.39% | 1 | FAIL |
| 2 | capital_com | median | 70 | 30.00% | 0.5681 | -9.40% | 10.39% | 1 | FAIL |
| 3 | capital_com | p95 | 70 | 30.00% | 0.5579 | -9.70% | 10.62% | 1 | FAIL |
| 4 | pepperstone | best_case | 55 | 43.64% | 1.1887 | +2.58% | 2.40% | 1 | FAIL |
| 5 | pepperstone | median | 55 | 43.64% | 1.1887 | +2.58% | 2.40% | 1 | FAIL |
| 6 | pepperstone | p95 | 55 | 43.64% | 1.1687 | +2.31% | 2.42% | 1 | FAIL |
| 7 | dukascopy | best_case | 46 | 45.65% | 1.1937 | +2.13% | 2.28% | 4 | FAIL |
| 8 | dukascopy | median | 46 | 45.65% | 1.1854 | +2.02% | 2.30% | 4 | FAIL |
| 9 | dukascopy | p95 | 46 | 45.65% | 1.0930 | +1.03% | 2.50% | 4 | FAIL |

## Gate Snapshot

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| PF cells >= 1.30 | 0/9 | >= 7/9 | FAIL |
| Trade-count cells >= 40 | 9/9 | 9/9 | PASS |
| Total matrix trades | 513 | Informational | PASS |
| Max zero-trade months | 4 | <= 3 | FAIL |
| Cross-broker persistence | Capital.com negative; Pepperstone/Dukascopy below threshold | Robust across windows | FAIL |
| Concentration | Dukascopy top-five contribution > 100% of net PnL | Must not depend on few trades | FAIL |

## Interpretation

VIX/VXV term-structure inversion is a sharper stress measure than absolute VIX, but this H1 exhaustion-reversal expression is not robust enough. The mild Pepperstone/Dukascopy pockets do not offset the negative Capital.com block and do not meet the Phase 0 PF gate.

## Next Action

Do not tune this v0 candidate. Future volatility research should require a materially different signal, such as options skew, realized/implied volatility spread, or primary intraday futures/options data.
