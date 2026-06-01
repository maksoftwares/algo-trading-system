# H4 SPY/TLT Risk-Rotation Reversal v0 First Pass

Generated: 2026-06-01
Status: `REJECTED_FIRST_PASS`

## Decision

Reject `h4_spy_tlt_risk_rotation_reversal_v0` without tuning.

The candidate was SHA256-locked before the run and passed synthetic smoke. The real matrix had enough trades in all cells, but the edge was too weak and failed cross-broker persistence.

## Summary

- Total cost-cell trades: 435
- PF cells >= 1.30: 0/9
- Trade-count cells >= 40: 9/9
- Best PF: 1.1291
- Best cell: cell 1 / capital_com / best_case
- Main failure: expectancy was below threshold everywhere; Capital.com was mildly positive below threshold, Pepperstone and Dukascopy were negative.

## Matrix

| Cell | Broker | Cost | Trades | Win rate | PF | Avg R | PnL USD | Max zero months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 44 | 50.00% | 1.1291 | 0.0561 | 118.70 | 2 |
| 2 | capital_com | median | 44 | 50.00% | 1.1291 | 0.0561 | 118.70 | 2 |
| 3 | capital_com | p95 | 44 | 50.00% | 1.1241 | 0.0539 | 113.88 | 2 |
| 4 | pepperstone | best_case | 54 | 42.59% | 0.9008 | -0.0423 | -119.41 | 2 |
| 5 | pepperstone | median | 54 | 42.59% | 0.9008 | -0.0423 | -119.41 | 2 |
| 6 | pepperstone | p95 | 54 | 40.74% | 0.8930 | -0.0461 | -129.53 | 2 |
| 7 | dukascopy | best_case | 47 | 36.17% | 0.7413 | -0.1200 | -282.83 | 2 |
| 8 | dukascopy | median | 47 | 36.17% | 0.7295 | -0.1268 | -298.38 | 2 |
| 9 | dukascopy | p95 | 47 | 36.17% | 0.7090 | -0.1386 | -325.30 | 2 |

## Interpretation

This candidate solved the sample-size problem but did not show an edge. Because PF persistence failed 0/9 and cross-broker transfer failed, no decile, multisymbol, or Gate 9 work is justified for v0.

Do not tune v0 thresholds. Any future SPY/TLT risk-rotation revisit needs a new versioned hypothesis and fresh SHA256 registration, preferably with a materially different mechanism rather than a threshold edit.
