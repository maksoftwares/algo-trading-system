# H1 Credit Spread Shock Follow-Through v0 First Pass

Generated: 2026-05-30
Status: `REJECTED_FIRST_PASS`

## Decision

Reject `h1_credit_spread_shock_followthrough_v0` without tuning.

This candidate tested whether shifted corporate-credit spread shocks continue through H1 XAUUSD after local price has already aligned with the credit-stress or credit-relief state. It solved sample size, but failed PF persistence with 0/9 cells above 1.30. Pepperstone was positive below threshold, while Capital.com and Dukascopy were negative across all cost cases.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero Months | Result |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | capital_com | best_case | 256 | 37.89% | 0.8140 | -13.21% | 16.19% | 0 | FAIL |
| 2 | capital_com | median | 256 | 37.89% | 0.8140 | -13.21% | 16.19% | 0 | FAIL |
| 3 | capital_com | p95 | 256 | 37.89% | 0.7955 | -14.51% | 17.01% | 0 | FAIL |
| 4 | pepperstone | best_case | 200 | 43.00% | 1.1010 | +5.56% | 9.91% | 2 | FAIL |
| 5 | pepperstone | median | 200 | 43.00% | 1.1010 | +5.56% | 9.91% | 2 | FAIL |
| 6 | pepperstone | p95 | 200 | 43.00% | 1.0794 | +4.36% | 10.10% | 2 | FAIL |
| 7 | dukascopy | best_case | 234 | 33.33% | 0.7124 | -18.53% | 22.34% | 0 | FAIL |
| 8 | dukascopy | median | 234 | 33.33% | 0.6944 | -19.50% | 22.93% | 0 | FAIL |
| 9 | dukascopy | p95 | 234 | 33.33% | 0.6708 | -20.71% | 23.88% | 0 | FAIL |

## Gate Snapshot

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| PF cells >= 1.30 | 0/9 | >= 7/9 | FAIL |
| Trade-count cells >= 40 | 9/9 | 9/9 | PASS |
| Total matrix trades | 2,070 | Informational | PASS |
| Max zero-trade months | 2 | <= 3 | PASS |
| Cross-broker persistence | Pepperstone-only positive below threshold | Robust across windows | FAIL |
| Best observed PF | 1.1010 | >= 1.30 in most cells | FAIL |

## Interpretation

The paired credit-spread follow-through expression improved activity and avoided the sparse-sample problem, but did not reveal a robust independent edge. The corporate credit-spread family now has failed H4 stress momentum, H1 shock reversal, and H1 shock follow-through expressions.

## Next Action

Do not tune v0. Treat shifted daily BAA/AAA credit-spread shocks as exhausted in the current-data lane unless a materially different credit input, such as full-history high-yield OAS, CDS, or intraday credit futures, becomes available before testing.
