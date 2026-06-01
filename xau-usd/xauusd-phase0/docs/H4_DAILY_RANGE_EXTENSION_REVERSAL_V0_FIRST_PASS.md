# H4 Daily Range Extension Reversal v0 First Pass

Generated: 2026-06-01
Status: `REJECTED_FIRST_PASS`

## Decision

Reject `h4_daily_range_extension_reversal_v0` without tuning.

This was a true H4/D1 OHLC-only diversification attempt, not a breakout-retest or level-pullback variant. It passed the synthetic smoke boundary and produced enough trades in all 9 real-data cells, but it failed the core edge gate: 0/9 cells reached PF >= 1.30. All broker/cost windows were negative after costs.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero Months | Single Trade | Top 5 | Result |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | capital_com | best_case | 64 | 45.31% | 0.9588 | -0.42% | 2.99% | 3 | 100.00% | 100.00% | FAIL |
| 2 | capital_com | median | 64 | 45.31% | 0.9588 | -0.42% | 2.99% | 3 | 100.00% | 100.00% | FAIL |
| 3 | capital_com | p95 | 64 | 45.31% | 0.9464 | -0.54% | 3.05% | 3 | 100.00% | 100.00% | FAIL |
| 4 | pepperstone | best_case | 40 | 40.00% | 0.6749 | -2.54% | 2.55% | 3 | 100.00% | 100.00% | FAIL |
| 5 | pepperstone | median | 40 | 40.00% | 0.6749 | -2.54% | 2.55% | 3 | 100.00% | 100.00% | FAIL |
| 6 | pepperstone | p95 | 40 | 40.00% | 0.6696 | -2.60% | 2.60% | 3 | 100.00% | 100.00% | FAIL |
| 7 | dukascopy | best_case | 67 | 44.78% | 0.9365 | -0.62% | 1.97% | 2 | 100.00% | 100.00% | FAIL |
| 8 | dukascopy | median | 67 | 44.78% | 0.9163 | -0.82% | 2.09% | 2 | 100.00% | 100.00% | FAIL |
| 9 | dukascopy | p95 | 67 | 44.78% | 0.8992 | -0.99% | 2.19% | 2 | 100.00% | 100.00% | FAIL |

## Gate Snapshot

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| PF cells >= 1.30 | 0/9 | >= 7/9 | FAIL |
| Trade-count cells >= 40 | 9/9 | 9/9 | PASS |
| Total matrix trades | 513 | Informational | PASS |
| Max zero-trade months | 3 | <= 3 | PASS |
| Largest single trade contribution | 100.00% | <= 10% | FAIL |
| Top-5 trade contribution | 100.00% | <= 40% | FAIL |
| P95 cost robustness | No broker/cost window reached PF 1.30 | Must remain buildable under P95 | FAIL |

## Interpretation

The idea did what we wanted from a process perspective: it was H4-cadenced, cost-resistant in structure, pre-registered, and had enough sample size. The market evidence was still not there. The rejection is mostly an edge failure rather than a frequency failure.

This also reinforces the current research pattern: slower OHLC-only XAU reversals are not automatically solving the breakout-retest family's cost/concentration problem.

## Next Action

Do not tune v0. The next higher-timeframe search should move to a genuinely different data source or behavior class, preferably primary COMEX/CME participation, order-flow, or options-skew evidence rather than another OHLC-only range variant.
