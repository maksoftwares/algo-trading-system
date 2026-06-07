# H4 GLD GVZ Vol Flow Reversal v0 First Pass

Generated: 2026-06-07

Expert: `h4_gld_gvz_vol_flow_reversal_v0`
Hypothesis SHA256: `9275835877d896871983aaf8663af88a61392e72fa6615925c2aca9751cbf59a`
Status: `REJECTED_FIRST_PASS`

## Verdict

Reject v0 without tuning.

The candidate passed the measured-cost structural precheck, focused unit test, hypothesis registration, and research smoke, but the real-data matrix produced a sparse Pepperstone-only PF pocket rather than a robust independent EA. It failed trade count in every cell and did not transfer to Capital.com or Dukascopy.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Return % | Max DD % | Losing months % | Max zero months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 12 | 25.00% | 0.4337 | -1.78% | 2.18% | 16.67% | 9 |
| 2 | capital_com | median | 12 | 25.00% | 0.4337 | -1.78% | 2.18% | 16.67% | 9 |
| 3 | capital_com | p95 | 12 | 25.00% | 0.4215 | -1.83% | 2.19% | 16.67% | 9 |
| 4 | pepperstone | best_case | 26 | 53.85% | 1.4347 | 1.63% | 1.04% | 11.11% | 4 |
| 5 | pepperstone | median | 26 | 53.85% | 1.4347 | 1.63% | 1.04% | 11.11% | 4 |
| 6 | pepperstone | p95 | 26 | 50.00% | 1.4243 | 1.60% | 1.05% | 11.11% | 4 |
| 7 | dukascopy | best_case | 18 | 50.00% | 0.9873 | -0.05% | 3.02% | 13.89% | 11 |
| 8 | dukascopy | median | 18 | 50.00% | 0.9732 | -0.11% | 3.02% | 13.89% | 11 |
| 9 | dukascopy | p95 | 18 | 50.00% | 0.9427 | -0.23% | 3.09% | 13.89% | 11 |

## Gate Snapshot

| Gate | Result |
| --- | --- |
| Measured-cost structural precheck | PASS, P95 cost_R 0.1875 |
| Focused unit test | PASS |
| Research candidate smoke | PASS, 1 synthetic signal |
| PF >= 1.30 in at least 7/9 cells | FAIL, 3/9 |
| At least 40 trades per cell | FAIL, 0/9 |
| Positive PnL persistence | FAIL, 3/9 and Pepperstone-only |
| Max zero-trade months <= 3 | FAIL, max 11 |
| Cross-broker persistence | FAIL, Capital.com negative and Dukascopy flat-negative |
| Concentration | FAIL, top-trade concentration remains extreme |

## Interpretation

Combining GLD flow stress with GVZ/VIX gold-volatility premium did not rescue either public proxy lane. It created a cleaner Pepperstone pocket than many proxy attempts, but the sample is too small and broker transfer is absent. This should be preserved as evidence, not promoted.

Do not tune v0. The higher-value next step remains acquiring primary COMEX/CME options, futures participation, or order-flow data.

## Evidence

- Hypothesis: `docs/hypothesis_h4_gld_gvz_vol_flow_reversal_v0.md`
- Cost precheck: `PASS`, median stop 400 points, P95 cost_R 0.1875
- Registration: `outputs/reports/h4_gld_gvz_vol_flow_reversal_v0_research_hypothesis_registration.md`
- Smoke: `outputs/reports/h4_gld_gvz_vol_flow_reversal_v0_research_smoke.md`
- Matrix: `outputs/matrix_results/h4_gld_gvz_vol_flow_reversal_v0/`
