# H1 DBC/UUP Commodity-Dollar Follow-Through v0 First-Pass Result

Status: `REJECTED_FIRST_PASS`
Date: 2026-05-29
Expert: `h1_dbc_uup_commodity_dollar_followthrough_v0`
Hypothesis SHA256: `523b8bc25748cce9dc0b9c6f0fb3389327025c71ac9b20e3d18de740744428cf`

## Hypothesis

This candidate tested whether XAUUSD follows broad commodity pressure against the dollar, using shifted daily DBC and UUP ETF observations, after H1 XAU price confirms in the same direction.

## Matrix Result

| Cell | Broker | Cost | Trades | Win rate | PF | Return | Zero months | Max DD |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 165 | 40.00% | 0.9091 | -4.08% | 1 | 5.78% |
| 2 | capital_com | median | 165 | 40.00% | 0.9091 | -4.08% | 1 | 5.78% |
| 3 | capital_com | p95 | 165 | 40.00% | 0.8825 | -5.29% | 1 | 6.19% |
| 4 | pepperstone | best_case | 157 | 42.04% | 1.0629 | 2.63% | 1 | 4.51% |
| 5 | pepperstone | median | 157 | 42.04% | 1.0629 | 2.63% | 1 | 4.51% |
| 6 | pepperstone | p95 | 157 | 42.04% | 1.0397 | 1.67% | 1 | 4.57% |
| 7 | dukascopy | best_case | 144 | 40.28% | 0.9445 | -2.08% | 1 | 8.80% |
| 8 | dukascopy | median | 144 | 40.28% | 0.9221 | -2.90% | 1 | 9.30% |
| 9 | dukascopy | p95 | 144 | 40.28% | 0.8761 | -4.59% | 1 | 10.25% |

## Gate Summary

- PF cells >= 1.30: `0/9`, required `7/9`.
- Trade-count cells >= 40: `9/9`.
- Total matrix trades across cost cells: `1,398`.
- Pepperstone was positive but below threshold.
- Capital.com and Dukascopy were negative across all cost cases.

## Decision

Reject v0 without tuning. The DBC/UUP commodity-dollar data class produced adequate sample size, but it did not produce cross-broker edge persistence and failed the core PF gate.
