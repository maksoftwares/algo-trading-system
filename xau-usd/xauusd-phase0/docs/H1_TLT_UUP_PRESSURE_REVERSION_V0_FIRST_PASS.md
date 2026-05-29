# H1 TLT/UUP Pressure Reversion v0 First-Pass Result

Status: `REJECTED_FIRST_PASS`
Date: 2026-05-29
Expert: `h1_tlt_uup_pressure_reversion_v0`
Hypothesis SHA256: `584f37b3962aefa6685068473ac4b36b8c5bdf1e45e0736d0fdeb65b69154e33`

## Hypothesis

This candidate tested whether XAUUSD reverts after temporarily moving against a traded rates/dollar pressure proxy built from shifted daily TLT and UUP ETF observations.

## Matrix Result

| Cell | Broker | Cost | Trades | Win rate | PF | Return | Zero months | Max DD |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 119 | 42.02% | 0.8748 | -3.66% | 0 | 5.35% |
| 2 | capital_com | median | 119 | 42.02% | 0.8748 | -3.66% | 0 | 5.35% |
| 3 | capital_com | p95 | 119 | 42.02% | 0.8523 | -4.34% | 0 | 5.89% |
| 4 | pepperstone | best_case | 140 | 38.57% | 0.8003 | -7.57% | 1 | 7.73% |
| 5 | pepperstone | median | 140 | 38.57% | 0.8003 | -7.57% | 1 | 7.73% |
| 6 | pepperstone | p95 | 140 | 37.86% | 0.7808 | -8.30% | 1 | 8.42% |
| 7 | dukascopy | best_case | 124 | 37.10% | 0.6779 | -10.45% | 1 | 10.67% |
| 8 | dukascopy | median | 124 | 37.10% | 0.6630 | -10.94% | 1 | 11.13% |
| 9 | dukascopy | p95 | 124 | 34.68% | 0.6237 | -12.13% | 1 | 12.28% |

## Gate Summary

- PF cells >= 1.30: `0/9`, required `7/9`.
- Trade-count cells >= 40: `9/9`.
- Total matrix trades across cost cells: `1,149`.
- Every broker window was negative.

## Decision

Reject v0 without tuning. The TLT/UUP pressure data class has enough activity, but the pre-registered reversion interpretation is directionally wrong across all broker windows. The paired follow-through interpretation may be tested as a separate locked candidate.
