# H1 TLT/UUP Pressure Follow-Through v0 First-Pass Result

Status: `REJECTED_FIRST_PASS`
Date: 2026-05-29
Expert: `h1_tlt_uup_pressure_followthrough_v0`
Hypothesis SHA256: `dbde4ff5888db0ed02183621447976bcd70b872f633a1098aeebf5ad641b0389`

## Hypothesis

This candidate tested whether XAUUSD follows a traded rates/dollar pressure proxy built from shifted daily TLT and UUP ETF observations, after H1 price confirms in the same direction.

## Matrix Result

| Cell | Broker | Cost | Trades | Win rate | PF | Return | Zero months | Max DD |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 174 | 40.23% | 0.8998 | -4.78% | 1 | 8.86% |
| 2 | capital_com | median | 174 | 40.23% | 0.8998 | -4.78% | 1 | 8.86% |
| 3 | capital_com | p95 | 174 | 39.66% | 0.8768 | -5.88% | 1 | 9.59% |
| 4 | pepperstone | best_case | 144 | 47.92% | 1.2716 | 9.91% | 2 | 5.90% |
| 5 | pepperstone | median | 144 | 47.92% | 1.2716 | 9.91% | 2 | 5.90% |
| 6 | pepperstone | p95 | 144 | 47.92% | 1.2371 | 8.66% | 2 | 6.18% |
| 7 | dukascopy | best_case | 173 | 42.20% | 0.9664 | -1.59% | 1 | 12.29% |
| 8 | dukascopy | median | 173 | 42.20% | 0.9494 | -2.37% | 1 | 12.53% |
| 9 | dukascopy | p95 | 173 | 41.62% | 0.9076 | -4.28% | 1 | 13.31% |

## Gate Summary

- PF cells >= 1.30: `0/9`, required `7/9`.
- Trade-count cells >= 40: `9/9`.
- Total matrix trades across cost cells: `1,473`.
- Pepperstone was positive but remained below threshold.
- Capital.com and Dukascopy were negative across all cost cases.

## Decision

Reject v0 without tuning. The TLT/UUP data class produced adequate sample size in both reversion and follow-through forms, but neither interpretation produced cross-broker edge.
