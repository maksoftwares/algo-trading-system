# H1 CNY-Dollar Pressure Reversion v0 First Pass

Generated: 2026-05-30
Status: `REJECTED_FIRST_PASS`

## Decision

Reject `h1_cny_dollar_pressure_reversion_v0` without tuning.

This candidate tested whether official FRED CNY-dollar pressure becomes locally exhausted on H1 XAUUSD after spot rejects continuation in the pressure-consistent direction. It found a strong but under-sampled Capital.com pocket, while Pepperstone and Dukascopy were negative across all cost cases. The candidate failed the trade-count floor in every cell and only 3/9 cells reached PF >= 1.30.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero Months | Result |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | capital_com | best_case | 25 | 60.00% | 2.0324 | +4.57% | 2.36% | 7 | FAIL |
| 2 | capital_com | median | 25 | 60.00% | 2.0324 | +4.57% | 2.36% | 7 | FAIL |
| 3 | capital_com | p95 | 25 | 60.00% | 1.9681 | +4.33% | 2.39% | 7 | FAIL |
| 4 | pepperstone | best_case | 38 | 34.21% | 0.7143 | -3.31% | 4.59% | 3 | FAIL |
| 5 | pepperstone | median | 38 | 34.21% | 0.7143 | -3.31% | 4.59% | 3 | FAIL |
| 6 | pepperstone | p95 | 38 | 34.21% | 0.7056 | -3.42% | 4.68% | 3 | FAIL |
| 7 | dukascopy | best_case | 30 | 36.67% | 0.6614 | -2.92% | 4.54% | 3 | FAIL |
| 8 | dukascopy | median | 30 | 33.33% | 0.6269 | -3.23% | 4.71% | 3 | FAIL |
| 9 | dukascopy | p95 | 30 | 30.00% | 0.5990 | -3.47% | 4.82% | 3 | FAIL |

## Gate Snapshot

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| PF cells >= 1.30 | 3/9 | >= 7/9 | FAIL |
| Trade-count cells >= 40 | 0/9 | 9/9 | FAIL |
| Total matrix trades | 279 | Informational | PASS |
| Max zero-trade months | 7 | <= 3 | FAIL |
| Cross-broker persistence | Capital.com-only positive pocket | Robust across windows | FAIL |
| Best observed PF | 2.0324 | >= 1.30 in most cells | FAIL |

## Interpretation

The reversion expression did expose a positive Capital.com pocket, but it is too sparse and does not replicate across broker windows. The paired CNY-dollar pressure family has now failed both follow-through and reversion expressions: follow-through solved sample size but failed PF, while reversion found a pocket but failed sample size, activity, and cross-broker persistence.

## Next Action

Do not tune v0. Treat official CNY-dollar pressure as an exhausted current-data lane unless a materially different source or timing mechanism is introduced before testing.
