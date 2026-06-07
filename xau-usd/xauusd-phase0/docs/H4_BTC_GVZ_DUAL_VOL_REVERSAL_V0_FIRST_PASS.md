# H4 BTC GVZ Dual Vol Reversal v0 First Pass

Generated: 2026-06-07

Expert: `h4_btc_gvz_dual_vol_reversal_v0`
Hypothesis SHA256: `a302f9cf9c0dca62179662245208e695c4342a581fd77ad825e5452e2123769e`
Status: `REJECTED_FIRST_PASS_SPARSE_PF_LEAD`

## Verdict

Reject v0 without tuning.

This candidate passed the focused unit test, measured-cost structural precheck, hypothesis registration, and research smoke. The real matrix produced a useful BTC+GVZ clue: Capital.com and Pepperstone reached PF above 1.30 across all cost cases, and 8 of 9 cells were non-negative. However, the edge is far too sparse and inactive for approval. Trade counts were only 10-21 per cell, no cell reached the 40-trade minimum, max zero-trade months reached 11, and Dukascopy failed the PF threshold with P95 turning negative.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Total PnL USD | Losing months % | Max zero months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 10 | 50.00% | 1.4949 | 85.97 | 8.33% | 11 |
| 2 | capital_com | median | 10 | 50.00% | 1.4949 | 85.97 | 8.33% | 11 |
| 3 | capital_com | p95 | 10 | 50.00% | 1.4799 | 83.81 | 8.33% | 11 |
| 4 | pepperstone | best_case | 21 | 52.38% | 1.6054 | 169.36 | 13.89% | 6 |
| 5 | pepperstone | median | 21 | 52.38% | 1.6054 | 169.36 | 13.89% | 6 |
| 6 | pepperstone | p95 | 21 | 52.38% | 1.5921 | 166.52 | 13.89% | 6 |
| 7 | dukascopy | best_case | 16 | 43.75% | 1.0152 | 5.06 | 19.44% | 10 |
| 8 | dukascopy | median | 16 | 43.75% | 1.0008 | 0.26 | 19.44% | 10 |
| 9 | dukascopy | p95 | 16 | 43.75% | 0.9468 | -17.64 | 19.44% | 10 |

## Gate Snapshot

| Gate | Result |
| --- | --- |
| Measured-cost structural precheck | PASS, median stop 400 points, P95 cost_R 0.1875 |
| Focused unit test | PASS |
| Research candidate smoke | PASS, 1 synthetic signal |
| PF >= 1.30 in at least 7/9 cells | FAIL, 6/9 |
| At least 40 trades per cell | FAIL, 0/9 |
| Positive PnL persistence | FAIL, 8/9 positive but Dukascopy P95 negative |
| Max zero-trade months <= 3 | FAIL, max 11 |
| Cross-broker persistence | FAIL, Dukascopy did not reach threshold |
| Concentration | FAIL, top-trade concentration is extreme |

## Interpretation

The combined BTC-volatility plus GVZ/VIX gold-volatility premium state is the best fresh BTC clue after the strict BTC stress reversal. It suggests that BTC volatility can help only when gold-specific volatility is also elevated. But v0 is not an EA candidate: it is too sparse, too concentrated, and not robust enough across Dukascopy/cost stress.

Do not tune v0. A future version would need a pre-registered activity-broadening mechanism that preserves the Capital.com/Pepperstone PF pocket while solving Dukascopy transfer. The current result is evidence for a research lead, not approval.

## Evidence

- Hypothesis: `docs/hypothesis_h4_btc_gvz_dual_vol_reversal_v0.md`
- Cost precheck: `PASS`, median stop 400 points, P95 cost_R 0.1875
- Registration: `outputs/reports/h4_btc_gvz_dual_vol_reversal_v0_research_hypothesis_registration.md`
- Smoke: `outputs/reports/h4_btc_gvz_dual_vol_reversal_v0_research_smoke.md`
- Matrix: `outputs/matrix_results/h4_btc_gvz_dual_vol_reversal_v0/`
