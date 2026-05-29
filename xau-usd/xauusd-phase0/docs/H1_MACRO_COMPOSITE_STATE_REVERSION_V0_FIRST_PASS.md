# H1 Macro Composite State Reversion v0 First-Pass Result

Status: `REJECTED_FIRST_PASS`
Date: 2026-05-29
Expert: `h1_macro_composite_state_reversion_v0`
Hypothesis SHA256: `4645199777dba51973a31d045deb6fef27d709dd78ebce8b56334daf6ad29d6f`

## Hypothesis

This candidate tested whether fixed macro-composite extremes create H1 XAUUSD overextension that reverts on a completed exhaustion candle. It used shifted macro inputs from the existing macro-composite stack: real yield, broad dollar, breakevens, Treasury curve, credit spreads, VIX, GVZ, and financial conditions.

## Matrix Result

| Cell | Broker | Cost | Trades | Win rate | PF | Return | Zero months | Max DD |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 8 | 25.00% | 0.4074 | -1.71% | 14 | 1.92% |
| 2 | capital_com | median | 8 | 25.00% | 0.4074 | -1.71% | 14 | 1.92% |
| 3 | capital_com | p95 | 8 | 25.00% | 0.3993 | -1.75% | 14 | 1.95% |
| 4 | pepperstone | best_case | 2 | 100.00% | inf | 1.12% | 20 | 0.00% |
| 5 | pepperstone | median | 2 | 100.00% | inf | 1.12% | 20 | 0.00% |
| 6 | pepperstone | p95 | 2 | 100.00% | inf | 1.12% | 20 | 0.00% |
| 7 | dukascopy | best_case | 21 | 38.10% | 0.8490 | -0.78% | 12 | 2.34% |
| 8 | dukascopy | median | 21 | 38.10% | 0.8347 | -0.84% | 12 | 2.28% |
| 9 | dukascopy | p95 | 21 | 38.10% | 0.7761 | -1.15% | 12 | 2.34% |

## Gate Summary

- PF cells >= 1.30: `3/9`, but all three are Pepperstone cells with only two trades.
- Trade-count cells >= 40: `0/9`.
- Total matrix trades across cost cells: `93`.
- Max zero-trade months reached `20`.

## Decision

Reject v0 without tuning. The macro-composite reversion idea is too sparse under the pre-registered H1 exhaustion definition, and the apparent Pepperstone PF is not meaningful with only two trades per cost cell.
