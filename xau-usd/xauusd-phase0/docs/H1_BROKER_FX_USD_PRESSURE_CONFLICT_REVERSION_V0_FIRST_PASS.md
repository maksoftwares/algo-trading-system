# H1 Broker FX USD Pressure Conflict Reversion v0 First Pass

Date: 2026-05-29
Status: REJECTED_FIRST_PASS
Expert: `h1_broker_fx_usd_pressure_conflict_reversion_v0`
Hypothesis SHA256: `3809bef6b1aeaa426d478087d818c4cdb22829b053aaa141d0b15bde35087bcf`

## Decision

Reject v0 without tuning.

The candidate showed a positive Capital.com pocket, but it failed the first-pass gate set. Only 3/9 cells reached PF >= 1.30 and only 3/9 cells reached the 40-trade floor. Pepperstone was materially negative and Dukascopy was roughly flat to slightly negative after higher costs.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero-Trade Months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Capital.com | best_case | 24 | 54.17% | 1.8697 | 3.41% | 0.97% | 0 |
| 2 | Capital.com | median | 24 | 54.17% | 1.8697 | 3.41% | 0.97% | 0 |
| 3 | Capital.com | p95 | 24 | 54.17% | 1.7969 | 3.18% | 0.99% | 0 |
| 4 | Pepperstone | best_case | 34 | 29.41% | 0.5107 | -4.99% | 4.99% | 0 |
| 5 | Pepperstone | median | 34 | 29.41% | 0.5107 | -4.99% | 4.99% | 0 |
| 6 | Pepperstone | p95 | 34 | 29.41% | 0.5041 | -5.09% | 5.09% | 0 |
| 7 | Dukascopy | best_case | 76 | 47.37% | 1.0608 | 0.96% | 3.92% | 0 |
| 8 | Dukascopy | median | 76 | 47.37% | 1.0191 | 0.30% | 4.02% | 0 |
| 9 | Dukascopy | p95 | 76 | 46.05% | 0.9718 | -0.45% | 4.12% | 0 |

## Gate Read

```text
PF >= 1.30 cells: 3/9
Trade-count cells >= 40 trades: 3/9
Total cost-cell trades: 402
First-pass decision: REJECTED_FIRST_PASS
```

## Interpretation

The conflict/catch-up interpretation produced too few trades in two broker windows and did not generalize outside the Capital.com pocket. It should not proceed to deciles, Gate 9, Phase 1 observation, Phase 2, or tuning under the same v0 hypothesis.
