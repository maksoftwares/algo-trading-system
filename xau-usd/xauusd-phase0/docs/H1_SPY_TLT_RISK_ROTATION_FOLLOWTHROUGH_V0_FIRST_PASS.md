# H1 SPY/TLT Risk Rotation Follow-Through v0 First-Pass Result

Status: `REJECTED_FIRST_PASS`
Date: 2026-05-29
Expert: `h1_spy_tlt_risk_rotation_followthrough_v0`
Hypothesis SHA256: `09728aacb39121730bb617e54fe53eb70a67a5d4dcb0abbe54f3244834b8af98`

## Hypothesis

This candidate tested whether XAUUSD follows a traded equity-vs-Treasury risk-rotation proxy built from shifted daily SPY and TLT ETF observations, after H1 XAU price confirms in the same direction.

## Matrix Result

| Cell | Broker | Cost | Trades | Win rate | PF | Return | Zero months | Max DD |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 177 | 44.63% | 1.0754 | 3.64% | 0 | 6.89% |
| 2 | capital_com | median | 177 | 44.63% | 1.0754 | 3.64% | 0 | 6.89% |
| 3 | capital_com | p95 | 177 | 44.63% | 1.0475 | 2.30% | 0 | 7.08% |
| 4 | pepperstone | best_case | 131 | 44.27% | 1.1709 | 5.68% | 2 | 3.91% |
| 5 | pepperstone | median | 131 | 44.27% | 1.1709 | 5.68% | 2 | 3.91% |
| 6 | pepperstone | p95 | 131 | 44.27% | 1.1540 | 5.13% | 2 | 3.98% |
| 7 | dukascopy | best_case | 169 | 38.46% | 0.8660 | -6.19% | 1 | 11.48% |
| 8 | dukascopy | median | 169 | 38.46% | 0.8453 | -7.10% | 1 | 11.90% |
| 9 | dukascopy | p95 | 169 | 37.87% | 0.8011 | -9.14% | 1 | 13.15% |

## Gate Summary

- PF cells >= 1.30: `0/9`, required `7/9`.
- Trade-count cells >= 40: `9/9`.
- Total matrix trades across cost cells: `1,431`.
- Capital.com and Pepperstone were positive but below PF threshold.
- Dukascopy was negative across all cost cases.

## Decision

Reject v0 without tuning. The SPY/TLT risk-rotation data class produced adequate sample size, but it did not produce cross-broker edge persistence and failed the core PF gate.
