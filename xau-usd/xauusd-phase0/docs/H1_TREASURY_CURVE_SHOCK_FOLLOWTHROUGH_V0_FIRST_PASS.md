# H1 Treasury Curve Shock Follow-Through v0 First Pass

Generated: 2026-05-30
Status: `REJECTED_FIRST_PASS`

## Decision

Reject `h1_treasury_curve_shock_followthrough_v0` without tuning.

This candidate tested whether shifted Treasury-rate / 2s10s curve shocks continue through H1 XAUUSD after local price has already aligned with the rate shock. It solved sample size, but failed PF persistence with 0/9 cells above 1.30. Capital.com was positive below threshold, Pepperstone was negative/flat, and Dukascopy was materially negative.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero Months | Result |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | capital_com | best_case | 172 | 45.93% | 1.1648 | +7.47% | 4.01% | 1 | FAIL |
| 2 | capital_com | median | 172 | 45.93% | 1.1648 | +7.47% | 4.01% | 1 | FAIL |
| 3 | capital_com | p95 | 172 | 45.93% | 1.1342 | +6.09% | 4.40% | 1 | FAIL |
| 4 | pepperstone | best_case | 122 | 40.16% | 0.9499 | -1.74% | 6.80% | 11 | FAIL |
| 5 | pepperstone | median | 122 | 40.16% | 0.9499 | -1.74% | 6.80% | 11 | FAIL |
| 6 | pepperstone | p95 | 122 | 40.16% | 0.9318 | -2.38% | 7.17% | 11 | FAIL |
| 7 | dukascopy | best_case | 180 | 34.44% | 0.7500 | -12.66% | 15.61% | 3 | FAIL |
| 8 | dukascopy | median | 180 | 34.44% | 0.7343 | -13.45% | 16.22% | 3 | FAIL |
| 9 | dukascopy | p95 | 180 | 34.44% | 0.7091 | -14.60% | 16.97% | 3 | FAIL |

## Gate Snapshot

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| PF cells >= 1.30 | 0/9 | >= 7/9 | FAIL |
| Trade-count cells >= 40 | 9/9 | 9/9 | PASS |
| Total matrix trades | 1,422 | Informational | PASS |
| Max zero-trade months | 11 | <= 3 | FAIL |
| Cross-broker persistence | Capital.com-only positive below threshold | Robust across windows | FAIL |
| Best observed PF | 1.1648 | >= 1.30 in most cells | FAIL |

## Interpretation

The paired Treasury-curve follow-through expression improved sample size versus many sparse macro ideas, but the edge does not persist across broker windows. The Treasury-curve family now has failed H4 stress momentum, H1 shock reversal, and H1 shock follow-through expressions.

## Next Action

Do not tune v0. Treat shifted daily Treasury-curve shocks as exhausted in the current-data lane unless a materially different intraday rates source or event-surprise mechanism is acquired before testing.
