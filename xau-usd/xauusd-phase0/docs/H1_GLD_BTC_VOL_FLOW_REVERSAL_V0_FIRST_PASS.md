# H1 GLD BTC Vol Flow Reversal v0 First Pass

Generated: 2026-06-07

Expert: `h1_gld_btc_vol_flow_reversal_v0`
Hypothesis SHA256: `58f31f9273feee832e7345928fa19748cf6b59441d6ab251d21e70617c3200bc`
Status: `REJECTED_FIRST_PASS_SPARSE_PF_LEAD_LOST`

## Verdict

Reject v0 without tuning.

The H1 execution variant did not solve the sparse-activity problem from the H4 GLD-flow plus BTC-volatility clue. It produced only 6 to 9 trades per cell, only Pepperstone stayed above PF 1.0, and no broker/cost cell reached the 1.30 PF threshold. This is not a worthy EA and does not justify deeper gates.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Return % | Max DD % | Losing months % | Max zero months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 8 | 25.00% | 0.8675 | -0.32% | 1.38% | 13.89% | 15 |
| 2 | capital_com | median | 8 | 25.00% | 0.8675 | -0.32% | 1.38% | 13.89% | 15 |
| 3 | capital_com | p95 | 8 | 25.00% | 0.8534 | -0.35% | 1.39% | 13.89% | 15 |
| 4 | pepperstone | best_case | 9 | 44.44% | 1.2907 | 0.54% | 0.98% | 8.33% | 12 |
| 5 | pepperstone | median | 9 | 44.44% | 1.2907 | 0.54% | 0.98% | 8.33% | 12 |
| 6 | pepperstone | p95 | 9 | 44.44% | 1.2783 | 0.52% | 0.99% | 8.33% | 12 |
| 7 | dukascopy | best_case | 6 | 33.33% | 0.8314 | -0.17% | 1.02% | 8.33% | 9 |
| 8 | dukascopy | median | 6 | 33.33% | 0.7187 | -0.31% | 1.07% | 8.33% | 9 |
| 9 | dukascopy | p95 | 6 | 33.33% | 0.7110 | -0.31% | 1.03% | 8.33% | 9 |

## Gate Snapshot

| Gate | Result |
| --- | --- |
| PF >= 1.30 in at least 7/9 cells | FAIL, 0/9 |
| At least 40 trades per cell | FAIL, 0/9 |
| Max zero-trade months <= 3 | FAIL, max 15 |
| Cross-broker persistence | FAIL, Pepperstone is only near-threshold and both Capital.com and Dukascopy are negative |
| Concentration | FAIL, sample is too sparse and largest/top-5 trade concentration is extreme |

## Interpretation

The H1 retest did the right thing as an experiment: it asked whether the H4 clue could be made more active by moving execution to H1 while keeping a materially similar GLD-flow plus BTC-volatility regime definition. The answer is no. H1 did not broaden the event count enough and it weakened the two-broker PF clue seen in H4.

Do not tune v0. A future BTC path should be independent rather than another threshold variant of GLD-flow plus BTC-volatility overlap.

## Evidence

- Hypothesis: `docs/hypothesis_h1_gld_btc_vol_flow_reversal_v0.md`
- Registration: `outputs/reports/h1_gld_btc_vol_flow_reversal_v0_research_hypothesis_registration.md`
- Smoke: `outputs/reports/h1_gld_btc_vol_flow_reversal_v0_research_smoke.md`
- Matrix: `outputs/matrix_results/h1_gld_btc_vol_flow_reversal_v0/`
