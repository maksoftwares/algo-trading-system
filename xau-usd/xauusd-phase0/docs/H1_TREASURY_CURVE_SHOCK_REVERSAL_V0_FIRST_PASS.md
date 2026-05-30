# H1 Treasury Curve Shock Reversal v0 First Pass

Generated: 2026-05-30
Status: `REJECTED_FIRST_PASS`

## Decision

Reject `h1_treasury_curve_shock_reversal_v0` without tuning.

This candidate produced enough trades in all 9 cells, but no cell reached PF >= 1.30. Capital.com and Dukascopy were mildly positive below threshold, Pepperstone was near flat, and the max zero-trade-month gate failed with 10.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero Months | Result |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | capital_com | best_case | 53 | 45.28% | 1.0677 | +0.96% | 2.98% | 3 | FAIL |
| 2 | capital_com | median | 53 | 45.28% | 1.0677 | +0.96% | 2.98% | 3 | FAIL |
| 3 | capital_com | p95 | 53 | 45.28% | 1.0510 | +0.73% | 3.04% | 3 | FAIL |
| 4 | pepperstone | best_case | 58 | 41.38% | 1.0140 | +0.22% | 4.46% | 10 | FAIL |
| 5 | pepperstone | median | 58 | 41.38% | 1.0140 | +0.22% | 4.46% | 10 | FAIL |
| 6 | pepperstone | p95 | 58 | 41.38% | 0.9949 | -0.08% | 4.49% | 10 | FAIL |
| 7 | dukascopy | best_case | 75 | 42.67% | 1.1172 | +2.31% | 4.48% | 3 | FAIL |
| 8 | dukascopy | median | 75 | 42.67% | 1.0991 | +1.94% | 4.37% | 3 | FAIL |
| 9 | dukascopy | p95 | 75 | 42.67% | 1.0440 | +0.86% | 4.64% | 3 | FAIL |

## Gate Snapshot

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| PF cells >= 1.30 | 0/9 | >= 7/9 | FAIL |
| Trade-count cells >= 40 | 9/9 | 9/9 | PASS |
| Total matrix trades | 558 | Informational | PASS |
| Max zero-trade months | 10 | <= 3 | FAIL |
| Cross-broker persistence | Mild positive pockets below threshold; no robust PF | Robust across windows | FAIL |
| Best observed PF | 1.1172 | >= 1.30 in most cells | FAIL |

## Interpretation

The shifted Treasury-rate and curve shock feature produced a smoother profile than many failed lanes, but the edge was too small and too inactive to meet Phase 0. It is not an approved EA candidate.

## Next Action

Do not tune this v0 candidate. Treat Treasury curve/rate shocks as tested in both H4 momentum and H1 reversal forms, with no approved independent EA.
