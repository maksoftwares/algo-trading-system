# H1 Financial Conditions Shock Follow-Through v0 First Pass

Generated: 2026-05-30
Status: `REJECTED_FIRST_PASS`

## Decision

Reject `h1_financial_conditions_shock_followthrough_v0` without tuning.

This candidate tested whether shifted NFCI/ANFCI financial-conditions shocks continue through H1 XAUUSD after local price has already aligned with the tightening or easing state. It solved sample size, but failed PF persistence with 0/9 cells above 1.30. Pepperstone was positive below threshold, while Capital.com and Dukascopy were negative across all cost cases.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero Months | Result |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | capital_com | best_case | 263 | 41.83% | 0.9681 | -2.34% | 8.54% | 4 | FAIL |
| 2 | capital_com | median | 263 | 41.83% | 0.9681 | -2.34% | 8.54% | 4 | FAIL |
| 3 | capital_com | p95 | 263 | 41.83% | 0.9422 | -4.22% | 9.78% | 4 | FAIL |
| 4 | pepperstone | best_case | 290 | 43.45% | 1.0933 | +7.16% | 8.20% | 2 | FAIL |
| 5 | pepperstone | median | 290 | 43.45% | 1.0933 | +7.16% | 8.20% | 2 | FAIL |
| 6 | pepperstone | p95 | 290 | 43.45% | 1.0768 | +5.88% | 8.67% | 2 | FAIL |
| 7 | dukascopy | best_case | 260 | 33.46% | 0.7195 | -20.48% | 25.46% | 6 | FAIL |
| 8 | dukascopy | median | 260 | 33.46% | 0.7027 | -21.44% | 26.28% | 6 | FAIL |
| 9 | dukascopy | p95 | 260 | 33.46% | 0.6693 | -23.53% | 27.99% | 6 | FAIL |

## Gate Snapshot

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| PF cells >= 1.30 | 0/9 | >= 7/9 | FAIL |
| Trade-count cells >= 40 | 9/9 | 9/9 | PASS |
| Total matrix trades | 2,439 | Informational | PASS |
| Max zero-trade months | 6 | <= 3 | FAIL |
| Cross-broker persistence | Pepperstone-only positive below threshold | Robust across windows | FAIL |
| Best observed PF | 1.0933 | >= 1.30 in most cells | FAIL |

## Interpretation

The paired financial-conditions follow-through expression improved activity and avoided the sparse-sample problem, but did not reveal a robust independent edge. The financial-conditions family now has failed H4 stress reversal, H1 shock reversal, and H1 shock follow-through expressions.

## Next Action

Do not tune v0. Treat shifted weekly NFCI/ANFCI financial-conditions shocks as exhausted in the current-data lane unless a materially different financial-stress input, such as intraday funding stress, credit futures, or options-skew data, becomes available before testing.
