# H4 BTC Whipsaw Gold Reversal v0 First Pass

Generated: 2026-06-07

Expert: `h4_btc_whipsaw_gold_reversal_v0`
Hypothesis SHA256: `cdbfeea0b7c741c108b1292b10c6339809d50cc5f7ff78baa02c2f3f34db8b4f`
Status: `REJECTED_FIRST_PASS`

## Verdict

Reject v0 without tuning.

The candidate passed the focused unit test, measured-cost structural precheck, hypothesis registration, and research smoke, but the real 9-cell matrix was negative in every broker/cost cell. The whipsaw state improved activity in Pepperstone and Dukascopy compared with several sparse BTC branches, but it destroyed expectancy: no cell reached PF 1.0, let alone the 1.30 threshold.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Total PnL USD | Losing months % | Max zero months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 29 | 41.38% | 0.6029 | -242.21 | 25.00% | 8 |
| 2 | capital_com | median | 29 | 41.38% | 0.6029 | -242.21 | 25.00% | 8 |
| 3 | capital_com | p95 | 29 | 41.38% | 0.5994 | -243.79 | 25.00% | 8 |
| 4 | pepperstone | best_case | 42 | 42.86% | 0.6536 | -277.27 | 33.33% | 4 |
| 5 | pepperstone | median | 42 | 42.86% | 0.6536 | -277.27 | 33.33% | 4 |
| 6 | pepperstone | p95 | 42 | 42.86% | 0.6477 | -283.23 | 33.33% | 4 |
| 7 | dukascopy | best_case | 56 | 35.71% | 0.7926 | -225.84 | 30.56% | 3 |
| 8 | dukascopy | median | 56 | 35.71% | 0.7038 | -328.61 | 30.56% | 3 |
| 9 | dukascopy | p95 | 56 | 33.93% | 0.6842 | -348.13 | 30.56% | 3 |

## Gate Snapshot

| Gate | Result |
| --- | --- |
| Measured-cost structural precheck | PASS, median stop 400 points, P95 cost_R 0.1875 |
| Focused unit test | PASS |
| Research candidate smoke | PASS, 1 synthetic signal |
| PF >= 1.30 in at least 7/9 cells | FAIL, 0/9 |
| At least 40 trades per cell | FAIL, 6/9 |
| Positive PnL persistence | FAIL, 0/9 |
| Max zero-trade months <= 3 | FAIL, max 8 |
| Cross-broker persistence | FAIL, every broker family was negative |
| Concentration | FAIL, top-trade concentration remains extreme |

## Interpretation

BTC path inefficiency is not a useful standalone filter for H4 XAU reversal under this rule set. It broadened the sample enough to show the idea clearly, and the answer was cleanly negative. This is better evidence than a sparse pocket: the edge is absent across all brokers and costs.

Do not tune v0. A future BTC candidate should probably use a genuinely different crypto data class or pair BTC with a stronger gold-primary context instead of another daily-OHLCV-derived BTC regime.

## Evidence

- Hypothesis: `docs/hypothesis_h4_btc_whipsaw_gold_reversal_v0.md`
- Cost precheck: `PASS`, median stop 400 points, P95 cost_R 0.1875
- Registration: `outputs/reports/h4_btc_whipsaw_gold_reversal_v0_research_hypothesis_registration.md`
- Smoke: `outputs/reports/h4_btc_whipsaw_gold_reversal_v0_research_smoke.md`
- Matrix: `outputs/matrix_results/h4_btc_whipsaw_gold_reversal_v0/`
