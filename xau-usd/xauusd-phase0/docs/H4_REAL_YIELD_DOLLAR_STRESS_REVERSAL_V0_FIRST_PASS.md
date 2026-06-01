# H4 Real-Yield Dollar Stress Reversal v0 First Pass

Generated: 2026-06-01
Status: `REJECTED_FIRST_PASS`

## Decision

Reject `h4_real_yield_dollar_stress_reversal_v0` without tuning.

The candidate was SHA256-locked before the run and passed synthetic smoke, but the real 9-cell matrix did not show enough edge, activity, or cross-broker persistence.

## Summary

- Total cost-cell trades: 189
- PF cells >= 1.30: 0/9
- Trade-count cells >= 40: 3/9
- Best PF: 1.2402
- Best cell: cell 7 / dukascopy / best_case
- Main failure: edge did not generalize; the only positive broker window was Dukascopy and it remained below the 1.30 PF threshold.

## Matrix

| Cell | Broker | Cost | Trades | Win rate | PF | Avg R | PnL USD | Max zero months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 11 | 36.36% | 0.5340 | -0.2608 | -143.58 | 9 |
| 2 | capital_com | median | 11 | 36.36% | 0.5340 | -0.2608 | -143.58 | 9 |
| 3 | capital_com | p95 | 11 | 36.36% | 0.5286 | -0.2653 | -145.98 | 9 |
| 4 | pepperstone | best_case | 9 | 44.44% | 0.7622 | -0.1147 | -52.56 | 15 |
| 5 | pepperstone | median | 9 | 44.44% | 0.7622 | -0.1147 | -52.56 | 15 |
| 6 | pepperstone | p95 | 9 | 44.44% | 0.7574 | -0.1175 | -53.80 | 15 |
| 7 | dukascopy | best_case | 43 | 46.51% | 1.2402 | 0.1083 | 229.27 | 3 |
| 8 | dukascopy | median | 43 | 46.51% | 1.2258 | 0.1027 | 217.02 | 3 |
| 9 | dukascopy | p95 | 43 | 46.51% | 1.1820 | 0.0836 | 175.37 | 3 |

## Interpretation

The hypothesis did test a genuinely different higher-timeframe macro-stress mechanism, but it was too sparse in Capital.com/Pepperstone and not strong enough in Dukascopy. Because PF persistence failed 0/9 and trade count failed 6/9, no decile, multisymbol, or Gate 9 work is justified for v0.

Do not tune v0 thresholds. Any future real-yield/dollar stress revisit needs a new versioned hypothesis and a fresh SHA256 registration.
