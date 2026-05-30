# H1 Policy Uncertainty Intraday Reversal v0 First Pass

Generated: 2026-05-30
Status: `REJECTED_FIRST_PASS`

## Decision

Reject `h1_policy_uncertainty_intraday_reversal_v0` without tuning.

This candidate produced a modest sample but failed the main matrix gate. No cell reached PF >= 1.30, and only 6 of 9 cells reached the 40-trade minimum. Pepperstone and Dukascopy had mild positive pockets below threshold, while Capital.com was negative across all cost cases.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero Months | Result |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | capital_com | best_case | 40 | 32.50% | 0.6509 | -4.39% | 4.48% | 3 | FAIL |
| 2 | capital_com | median | 40 | 32.50% | 0.6509 | -4.39% | 4.48% | 3 | FAIL |
| 3 | capital_com | p95 | 40 | 32.50% | 0.6252 | -4.75% | 4.81% | 3 | FAIL |
| 4 | pepperstone | best_case | 51 | 43.14% | 1.0756 | +1.03% | 4.67% | 3 | FAIL |
| 5 | pepperstone | median | 51 | 43.14% | 1.0756 | +1.03% | 4.67% | 3 | FAIL |
| 6 | pepperstone | p95 | 51 | 43.14% | 1.0694 | +0.94% | 4.61% | 3 | FAIL |
| 7 | dukascopy | best_case | 31 | 45.16% | 1.1276 | +1.01% | 3.80% | 2 | FAIL |
| 8 | dukascopy | median | 31 | 45.16% | 1.1320 | +1.04% | 3.72% | 2 | FAIL |
| 9 | dukascopy | p95 | 31 | 45.16% | 1.0628 | +0.50% | 3.76% | 2 | FAIL |

## Gate Snapshot

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| PF cells >= 1.30 | 0/9 | >= 7/9 | FAIL |
| Trade-count cells >= 40 | 6/9 | 9/9 | FAIL |
| Total matrix trades | 366 | Informational | PASS |
| Max zero-trade months | 3 | <= 3 | PASS |
| Cross-broker persistence | Capital.com negative; Pepperstone/Dukascopy below threshold | Robust across windows | FAIL |
| Best observed PF | 1.1320 | >= 1.30 in most cells | FAIL |

## Interpretation

The shifted US policy-uncertainty shock feature did not produce a robust intraday XAU reversal edge. The idea generated some positive lower-cost pockets, but the edge was too weak and too sparse to pass Phase 0 first pass.

## Next Action

Do not tune this v0 candidate. Treat the policy-uncertainty data class as tested in both H4 safe-haven continuation and H1 intraday reversal forms, with no approved independent EA.
