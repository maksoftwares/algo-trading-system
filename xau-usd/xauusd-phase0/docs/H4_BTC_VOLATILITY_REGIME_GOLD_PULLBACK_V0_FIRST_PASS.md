# H4 BTC Volatility Regime Gold Pullback v0 First Pass

Generated: 2026-06-07

Expert: `h4_btc_volatility_regime_gold_pullback_v0`
Hypothesis SHA256: `8290fb10a5646025dc290c23f43993a04073ef1d7f03a513dba75eaf301f5e8f`
Status: `REJECTED_FIRST_PASS`

## Verdict

Reject v0 without tuning.

The candidate passed the measured-cost structural precheck and produced small positive pockets in Capital.com and Pepperstone, but it did not become a worthy BTC-gated EA. It produced only 9 to 17 trades per cell, 0/9 PF cells above 1.30, 0/9 cells above the 40-trade floor, and negative Dukascopy results.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Return % | Max DD % | Losing months % | Max zero months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 9 | 44.44% | 1.2336 | 0.44% | 0.73% | 13.89% | 8 |
| 2 | capital_com | median | 9 | 44.44% | 1.2336 | 0.44% | 0.73% | 13.89% | 8 |
| 3 | capital_com | p95 | 9 | 44.44% | 1.2210 | 0.42% | 0.73% | 13.89% | 8 |
| 4 | pepperstone | best_case | 17 | 41.18% | 1.2301 | 0.61% | 3.18% | 13.89% | 4 |
| 5 | pepperstone | median | 17 | 41.18% | 1.2301 | 0.61% | 3.18% | 13.89% | 4 |
| 6 | pepperstone | p95 | 17 | 41.18% | 1.2211 | 0.59% | 3.19% | 13.89% | 4 |
| 7 | dukascopy | best_case | 13 | 38.46% | 0.8973 | -0.25% | 1.72% | 13.89% | 6 |
| 8 | dukascopy | median | 13 | 38.46% | 0.8673 | -0.32% | 1.72% | 13.89% | 6 |
| 9 | dukascopy | p95 | 13 | 38.46% | 0.8353 | -0.41% | 1.82% | 13.89% | 6 |

## Gate Snapshot

| Gate | Result |
| --- | --- |
| Measured-cost structural precheck | PASS, P95 cost_R 0.1875 |
| PF >= 1.30 in at least 7/9 cells | FAIL, 0/9 |
| At least 40 trades per cell | FAIL, 0/9 |
| Max zero-trade months <= 3 | FAIL, max 8 |
| Cross-broker persistence | FAIL, Dukascopy negative across all costs |
| Concentration | FAIL, top-trade concentration remains extreme |

## Interpretation

This falsifies the BTC-volatility pullback-continuation path. Compared with `h4_btc_volatility_regime_gold_breakout_v0`, the pullback version improved Capital.com/Pepperstone signs but collapsed activity and still did not transfer to Dukascopy. The result is useful evidence, but not a worthy EA.

Do not tune v0. A future BTC attempt needs either a stronger BTC data class than daily Yahoo OHLCV or a materially different mechanism.

## Evidence

- Hypothesis: `docs/hypothesis_h4_btc_volatility_regime_gold_pullback_v0.md`
- Cost precheck: `PASS`, median stop 400 points, P95 cost_R 0.1875
- Registration: `outputs/reports/h4_btc_volatility_regime_gold_pullback_v0_research_hypothesis_registration.md`
- Smoke: `outputs/reports/h4_btc_volatility_regime_gold_pullback_v0_research_smoke.md`
- Matrix: `outputs/matrix_results/h4_btc_volatility_regime_gold_pullback_v0/`
