# H4 BTC Risk Pressure Gold Reversal v1 First Pass

Date: 2026-06-07
Status: REJECTED_FIRST_PASS
Expert: `h4_btc_risk_pressure_gold_reversal_v1`
Hypothesis SHA256: `1ddde77f2edae3c7a1e2f237eaab3650f163ef27d3d73be199b8a113f245f5c8`

## Decision

Reject v1 without tuning.

The candidate broadened v0 enough to reach the 40-trade floor in Capital.com and Pepperstone, but the broader sample diluted PF below the 1.30 requirement and failed cross-broker persistence. Dukascopy produced only 37 trades per cell and all three Dukascopy cells were negative.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return % | Max DD % |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | Capital.com | best_case | 46 | 50.00% | 1.1952 | 1.63% | 2.34% |
| 2 | Capital.com | median | 46 | 50.00% | 1.1952 | 1.63% | 2.34% |
| 3 | Capital.com | p95 | 46 | 50.00% | 1.1791 | 1.51% | 2.36% |
| 4 | Pepperstone | best_case | 48 | 54.17% | 1.2934 | 2.52% | 2.80% |
| 5 | Pepperstone | median | 48 | 54.17% | 1.2934 | 2.52% | 2.80% |
| 6 | Pepperstone | p95 | 48 | 54.17% | 1.2833 | 2.45% | 2.81% |
| 7 | Dukascopy | best_case | 37 | 35.14% | 0.9141 | -0.62% | 3.41% |
| 8 | Dukascopy | median | 37 | 35.14% | 0.8556 | -1.07% | 3.54% |
| 9 | Dukascopy | p95 | 37 | 35.14% | 0.8247 | -1.31% | 3.65% |

## Gate Read

```text
PF >= 1.30 cells: 0/9
Trade-count cells >= 40 trades: 6/9
First-pass decision: REJECTED_FIRST_PASS
```

## Interpretation

The v1 broadening solved part of the activity problem but invalidated the cross-broker edge. The best reading is that v0's BTC stress-reversal clue may require stricter stress quality while only modestly increasing signal frequency. v1 should not proceed to deciles, multisymbol, Gate 9, Phase 1, Phase 2, demo, paper execution, or live execution.

Any continuation must use a new versioned hypothesis. Do not tune v1 in place.
