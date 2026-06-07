# H4 BTC Volatility Compression Gold Expansion v0 First Pass

Generated: 2026-06-07

Expert: `h4_btc_volatility_compression_gold_expansion_v0`
Hypothesis SHA256: `b182a859625b026ea1cbc3e346903074ce96d3865f84390e40ce12fb48585602`
Status: `REJECTED_FIRST_PASS`

## Verdict

Reject v0 without tuning.

The candidate passed the measured-cost structural precheck, focused unit test, and research smoke, but the real-data matrix decisively rejected the idea. It produced enough activity in Capital.com and Dukascopy windows, but every broker/cost cell lost money and 0/9 cells reached PF 1.30.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Return % | Max DD % | Losing months % | Max zero months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 49 | 36.73% | 0.7796 | -2.58% | 5.06% | 33.33% | 3 |
| 2 | capital_com | median | 49 | 36.73% | 0.7796 | -2.58% | 5.06% | 33.33% | 3 |
| 3 | capital_com | p95 | 49 | 36.73% | 0.7707 | -2.69% | 5.14% | 36.11% | 3 |
| 4 | pepperstone | best_case | 27 | 40.74% | 0.7362 | -1.68% | 2.71% | 27.78% | 8 |
| 5 | pepperstone | median | 27 | 40.74% | 0.7362 | -1.68% | 2.71% | 27.78% | 8 |
| 6 | pepperstone | p95 | 27 | 40.74% | 0.7302 | -1.73% | 2.72% | 27.78% | 8 |
| 7 | dukascopy | best_case | 46 | 39.13% | 0.6116 | -4.39% | 5.02% | 36.11% | 9 |
| 8 | dukascopy | median | 46 | 36.96% | 0.5586 | -5.06% | 5.50% | 36.11% | 9 |
| 9 | dukascopy | p95 | 46 | 36.96% | 0.5336 | -5.44% | 5.84% | 36.11% | 9 |

## Gate Snapshot

| Gate | Result |
| --- | --- |
| Measured-cost structural precheck | PASS, P95 cost_R 0.1875 |
| Focused unit test | PASS |
| Research candidate smoke | PASS, 1 synthetic signal |
| PF >= 1.30 in at least 7/9 cells | FAIL, 0/9 |
| At least 40 trades per cell | FAIL, 6/9 |
| Positive PnL persistence | FAIL, 0/9 |
| Max zero-trade months <= 3 | FAIL, max 9 |
| Cross-broker persistence | FAIL, all broker windows negative |
| Concentration | FAIL, top-trade concentration remains extreme |

## Interpretation

This falsifies the opposite BTC-volatility branch: BTC daily compression did not provide a useful context for H4 XAU expansion continuation. Compared with the high-volatility BTC branches, this version improved activity in two broker windows but turned the edge negative everywhere.

Do not tune v0. A future BTC attempt should be a new versioned hypothesis, not a threshold adjustment of this compression-expansion shape.

## Evidence

- Hypothesis: `docs/hypothesis_h4_btc_volatility_compression_gold_expansion_v0.md`
- Cost precheck: `PASS`, median stop 400 points, P95 cost_R 0.1875
- Unit test: `tests/test_h4_btc_volatility_compression_gold_expansion_v0.py`
- Smoke: `outputs/reports/h4_btc_volatility_compression_gold_expansion_v0_research_smoke.md`
- Matrix: `outputs/matrix_results/h4_btc_volatility_compression_gold_expansion_v0/`
