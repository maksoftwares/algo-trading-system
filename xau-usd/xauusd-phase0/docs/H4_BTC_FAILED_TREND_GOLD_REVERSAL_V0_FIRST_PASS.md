# H4 BTC Failed Trend Gold Reversal v0 First Pass

Generated: 2026-06-07

Expert: `h4_btc_failed_trend_gold_reversal_v0`
Hypothesis SHA256: `6bc2e2a6c72e6446128d2cd7e4477ddeb945ab66f6919e2cd7955d9dc5eb642c`
Status: `REJECTED_FIRST_PASS`

## Verdict

Reject v0 without tuning.

The candidate passed the measured-cost structural precheck, focused unit test, hypothesis registration, and research smoke, but the real-data matrix failed decisively. It produced a small Dukascopy-only PF pocket, but only 4 to 10 trades per cell, negative Capital.com/Pepperstone cells, and max zero-trade months reached 16.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Return % | Max DD % | Losing months % | Max zero months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 8 | 37.50% | 0.6345 | -0.89% | 1.93% | 11.11% | 14 |
| 2 | capital_com | median | 8 | 37.50% | 0.6345 | -0.89% | 1.93% | 11.11% | 14 |
| 3 | capital_com | p95 | 8 | 37.50% | 0.6263 | -0.91% | 1.94% | 11.11% | 14 |
| 4 | pepperstone | best_case | 10 | 30.00% | 0.5703 | -1.01% | 1.46% | 13.89% | 9 |
| 5 | pepperstone | median | 10 | 30.00% | 0.5703 | -1.01% | 1.46% | 13.89% | 9 |
| 6 | pepperstone | p95 | 10 | 30.00% | 0.5663 | -1.02% | 1.46% | 13.89% | 9 |
| 7 | dukascopy | best_case | 4 | 75.00% | 2.0538 | 0.47% | 0.44% | 2.78% | 16 |
| 8 | dukascopy | median | 4 | 75.00% | 1.9300 | 0.42% | 0.45% | 2.78% | 16 |
| 9 | dukascopy | p95 | 4 | 75.00% | 1.8370 | 0.39% | 0.46% | 2.78% | 16 |

## Gate Snapshot

| Gate | Result |
| --- | --- |
| Measured-cost structural precheck | PASS, P95 cost_R 0.1875 |
| Focused unit test | PASS |
| Research candidate smoke | PASS, 1 synthetic signal |
| PF >= 1.30 in at least 7/9 cells | FAIL, 3/9 |
| At least 40 trades per cell | FAIL, 0/9 |
| Positive PnL persistence | FAIL, 3/9 and Dukascopy-only |
| Max zero-trade months <= 3 | FAIL, max 16 |
| Cross-broker persistence | FAIL, Capital.com and Pepperstone negative |
| Concentration | FAIL, top-trade concentration remains extreme |

## Interpretation

BTC failed-trend context is too sparse in the current public daily proxy and does not transfer across brokers. The Dukascopy pocket is not approval-worthy because it is only four trades per cell and concentration is extreme.

Do not tune v0. Any future BTC candidate should avoid relying on rare 20-day/5-day trend-failure clusters unless a better BTC data class is added.

## Evidence

- Hypothesis: `docs/hypothesis_h4_btc_failed_trend_gold_reversal_v0.md`
- Cost precheck: `PASS`, median stop 400 points, P95 cost_R 0.1875
- Registration: `outputs/reports/h4_btc_failed_trend_gold_reversal_v0_research_hypothesis_registration.md`
- Smoke: `outputs/reports/h4_btc_failed_trend_gold_reversal_v0_research_smoke.md`
- Matrix: `outputs/matrix_results/h4_btc_failed_trend_gold_reversal_v0/`
