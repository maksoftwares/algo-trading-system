# H4 BTC Volume Climax Gold Reversal v0 First Pass

Generated: 2026-06-07

Expert: `h4_btc_volume_climax_gold_reversal_v0`
Hypothesis SHA256: `5571c31d1136e57729cc32b9330bbfd51d707a33213b455fe2dd2ef07f099cff`
Status: `REJECTED_FIRST_PASS`

## Verdict

Reject v0 without tuning.

BTC volume climax did not produce a useful XAU reversal edge. The candidate was sparse, negative across all brokers, and had 0/9 PF cells above 1.30. It is not a worthy EA and does not justify deeper gates.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Return % | Max DD % | Losing months % | Max zero months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 10 | 40.00% | 0.5760 | -0.82% | 1.69% | 13.89% | 11 |
| 2 | capital_com | median | 10 | 40.00% | 0.5760 | -0.82% | 1.69% | 13.89% | 11 |
| 3 | capital_com | p95 | 10 | 40.00% | 0.5666 | -0.84% | 1.71% | 13.89% | 11 |
| 4 | pepperstone | best_case | 10 | 40.00% | 0.3684 | -1.51% | 1.85% | 13.89% | 12 |
| 5 | pepperstone | median | 10 | 40.00% | 0.3684 | -1.51% | 1.85% | 13.89% | 12 |
| 6 | pepperstone | p95 | 10 | 40.00% | 0.3648 | -1.52% | 1.87% | 13.89% | 12 |
| 7 | dukascopy | best_case | 13 | 38.46% | 0.4419 | -1.62% | 2.09% | 13.89% | 12 |
| 8 | dukascopy | median | 13 | 38.46% | 0.3815 | -1.83% | 2.17% | 13.89% | 12 |
| 9 | dukascopy | p95 | 13 | 38.46% | 0.3648 | -1.91% | 2.24% | 13.89% | 12 |

## Gate Snapshot

| Gate | Result |
| --- | --- |
| PF >= 1.30 in at least 7/9 cells | FAIL, 0/9 |
| At least 40 trades per cell | FAIL, 0/9 |
| Max zero-trade months <= 3 | FAIL, max 12 |
| Cross-broker persistence | FAIL, all brokers negative |
| Concentration | FAIL, sample is too sparse and largest/top-5 trade concentration is extreme |

## Interpretation

This candidate tested a genuinely separate BTC feature class available in the current public proxy data: participation intensity instead of return pressure or realized-volatility expansion. The result is decisively negative. BTC volume climax by itself does not rescue the BTC branch under the current XAU H4 rejection execution rule.

Do not tune v0. Future BTC work should use a stronger or different crypto data class, such as funding, futures basis, stablecoin liquidity, exchange reserves, or order-flow breadth, if such data is acquired and can be shifted cleanly.

## Evidence

- Hypothesis: `docs/hypothesis_h4_btc_volume_climax_gold_reversal_v0.md`
- Registration: `outputs/reports/h4_btc_volume_climax_gold_reversal_v0_research_hypothesis_registration.md`
- Smoke: `outputs/reports/h4_btc_volume_climax_gold_reversal_v0_research_smoke.md`
- Matrix: `outputs/matrix_results/h4_btc_volume_climax_gold_reversal_v0/`
