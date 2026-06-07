# H4 GLD ETF Flow Reversal v3 First Pass

Generated: 2026-06-07

Expert: `h4_gld_etf_flow_reversal_v3`
Hypothesis SHA256: `597e03f6952a09bd300ec09b135779b650bc7f5c9e4b9c16d1b6a340a2bf1a66`
Status: `REJECTED_FIRST_PASS`

## Verdict

Reject v3 without tuning.

The timing expansion fixed the trade-count problem, but it did not restore the v0 GLD-flow PF lead across brokers. Dukascopy passed PF in all cost cells and Pepperstone stayed positive but below threshold. Capital.com was negative across costs, so the result is broker-fragmented rather than approval-worthy.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Return % | Max DD % | Losing months % | Max zero months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 42 | 47.62% | 0.8509 | -1.37% | 3.42% | 36.11% | 5 |
| 2 | capital_com | median | 42 | 47.62% | 0.8509 | -1.37% | 3.42% | 36.11% | 5 |
| 3 | capital_com | p95 | 42 | 47.62% | 0.8455 | -1.42% | 3.43% | 36.11% | 5 |
| 4 | pepperstone | best_case | 56 | 51.79% | 1.2261 | 2.41% | 3.92% | 27.78% | 3 |
| 5 | pepperstone | median | 56 | 51.79% | 1.2261 | 2.41% | 3.92% | 27.78% | 3 |
| 6 | pepperstone | p95 | 56 | 51.79% | 1.2176 | 2.33% | 3.93% | 27.78% | 3 |
| 7 | dukascopy | best_case | 57 | 47.37% | 1.5198 | 5.33% | 3.21% | 19.44% | 5 |
| 8 | dukascopy | median | 57 | 47.37% | 1.4436 | 4.58% | 3.38% | 19.44% | 5 |
| 9 | dukascopy | p95 | 57 | 47.37% | 1.4031 | 4.20% | 3.43% | 19.44% | 5 |

## Gate Snapshot

| Gate | Result |
| --- | --- |
| PF >= 1.30 in at least 7/9 cells | FAIL, 3/9 |
| At least 40 trades per cell | PASS, 9/9 |
| Max zero-trade months <= 3 | FAIL, max 5 |
| Cross-broker persistence | FAIL, threshold strength is Dukascopy-only |
| Concentration | FAIL context, Capital.com is negative and Pepperstone top-5 concentration remains high |

## Interpretation

The GLD-flow family remains the strongest independent clue, but v3 confirms the same trade-off as the earlier versions: enough activity dilutes the edge, while the remaining PF threshold strength does not generalize across brokers.

Do not tune v3. A future GLD-flow attempt needs a materially different mechanism, not another timing-window expansion.

## Evidence

- Hypothesis: `docs/hypothesis_h4_gld_etf_flow_reversal_v3.md`
- Registration: `outputs/reports/h4_gld_etf_flow_reversal_v3_research_hypothesis_registration.md`
- Smoke: `outputs/reports/h4_gld_etf_flow_reversal_v3_research_smoke.md`
- Matrix: `outputs/matrix_results/h4_gld_etf_flow_reversal_v3/`
