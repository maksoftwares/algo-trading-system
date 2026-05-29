# H1 Broker FX USD Pressure Follow-Through v0 First Pass

Date: 2026-05-29
Status: REJECTED_FIRST_PASS
Expert: `h1_broker_fx_usd_pressure_followthrough_v0`
Hypothesis SHA256: `237acc8d73453d92bef058b7b5372dd19d322687ddf5eedf2c2edc9fa50a75e2`

## Decision

Reject v0 without tuning.

The candidate reached the sample-size floor in all 9 cells and produced zero zero-trade months. It failed the first-pass edge gate because 0/9 cells reached PF >= 1.30. Capital.com and Pepperstone were positive but below threshold, while Dukascopy was strongly negative across all cost cases.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero-Trade Months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Capital.com | best_case | 287 | 46.34% | 1.1429 | 11.26% | 7.28% | 0 |
| 2 | Capital.com | median | 287 | 46.34% | 1.1429 | 11.26% | 7.28% | 0 |
| 3 | Capital.com | p95 | 287 | 46.34% | 1.1130 | 8.85% | 7.40% | 0 |
| 4 | Pepperstone | best_case | 196 | 41.84% | 1.0606 | 2.93% | 10.74% | 0 |
| 5 | Pepperstone | median | 196 | 41.84% | 1.0606 | 2.93% | 10.74% | 0 |
| 6 | Pepperstone | p95 | 196 | 41.84% | 1.0396 | 1.92% | 11.05% | 0 |
| 7 | Dukascopy | best_case | 277 | 38.27% | 0.8188 | -12.49% | 15.76% | 0 |
| 8 | Dukascopy | median | 277 | 37.55% | 0.7969 | -13.97% | 16.95% | 0 |
| 9 | Dukascopy | p95 | 277 | 36.46% | 0.7527 | -16.71% | 19.01% | 0 |

## Gate Read

```text
PF >= 1.30 cells: 0/9
Trade-count cells >= 40 trades: 9/9
Total cost-cell trades: 2,280
First-pass decision: REJECTED_FIRST_PASS
```

## Interpretation

Broker-consistent EURUSD/USDJPY H1 dollar-pressure is a useful independent data class to test, but this fixed direct-follow-through interpretation does not survive the matrix. The pattern is not robust across brokers and should not proceed to deciles, Gate 9, Phase 1 observation, Phase 2, or tuning under the same v0 hypothesis.
