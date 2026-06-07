# H1 BTC Risk Pressure Gold Followthrough v1 First Pass

Generated: 2026-06-07

Expert: `h1_btc_risk_pressure_gold_followthrough_v1`
Hypothesis SHA256: `7f70f5e5e837ce96531f0b7e8a884ad22e4cfef6a87cbe4fc0dcd9fbdfb6d8e0`
Status: `REJECTED_FIRST_PASS`

## Verdict

Reject v1 without tuning.

The asymmetric H1 BTC pressure follow-through rule did not produce cross-broker edge. Capital.com was barely positive and below threshold, Pepperstone was negative across costs, and Dukascopy was materially negative. The candidate also missed the 40-trade minimum in Capital.com and Dukascopy and exceeded the zero-trade-month gate.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Return % | Max DD % | Losing months % | Max zero months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 37 | 48.65% | 1.0144 | 0.12% | 2.20% | 25.00% | 8 |
| 2 | capital_com | median | 37 | 48.65% | 1.0144 | 0.12% | 2.20% | 25.00% | 8 |
| 3 | capital_com | p95 | 37 | 48.65% | 1.0003 | 0.00% | 2.22% | 25.00% | 8 |
| 4 | pepperstone | best_case | 51 | 31.37% | 0.6832 | -4.47% | 7.28% | 44.44% | 5 |
| 5 | pepperstone | median | 51 | 31.37% | 0.6832 | -4.47% | 7.28% | 44.44% | 5 |
| 6 | pepperstone | p95 | 51 | 31.37% | 0.6746 | -4.60% | 7.33% | 44.44% | 5 |
| 7 | dukascopy | best_case | 32 | 21.88% | 0.5613 | -3.33% | 3.34% | 44.44% | 4 |
| 8 | dukascopy | median | 32 | 21.88% | 0.4605 | -4.70% | 4.70% | 44.44% | 4 |
| 9 | dukascopy | p95 | 32 | 21.88% | 0.4014 | -5.57% | 5.57% | 44.44% | 4 |

## Gate Snapshot

| Gate | Result |
| --- | --- |
| PF >= 1.30 in at least 7/9 cells | FAIL, 0/9 |
| At least 40 trades per cell | FAIL, 3/9 |
| Max zero-trade months <= 3 | FAIL, max 8 |
| Cross-broker persistence | FAIL, Capital.com-only near-flat drift below threshold |
| Concentration | FAIL, small Capital.com profit is dominated by top trades and all other broker windows lose money |

## Interpretation

The v1 asymmetry reduced activity compared with v2 but did not improve persistence. Together, v1 and v2 show that this Yahoo BTC daily pressure family either becomes too sparse or broadens into negative cross-broker expectancy.

Do not tune v1. Future BTC work should use a materially different mechanism, such as BTC volatility regime transitions, crypto-liquidity breadth, or a separate XAU execution trigger not tied to the same BTC return-pressure gate.

## Evidence

- Hypothesis: `docs/hypothesis_h1_btc_risk_pressure_gold_followthrough_v1.md`
- Registration: `outputs/reports/h1_btc_risk_pressure_gold_followthrough_v1_research_hypothesis_registration.md`
- Smoke: `outputs/reports/h1_btc_risk_pressure_gold_followthrough_v1_research_smoke.md`
- Matrix: `outputs/matrix_results/h1_btc_risk_pressure_gold_followthrough_v1/`
