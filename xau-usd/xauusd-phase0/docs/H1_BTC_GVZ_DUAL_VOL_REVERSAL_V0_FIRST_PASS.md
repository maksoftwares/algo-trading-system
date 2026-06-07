# H1 BTC GVZ Dual Vol Reversal v0 First Pass

Generated: 2026-06-07

Expert: `h1_btc_gvz_dual_vol_reversal_v0`
Hypothesis SHA256: `b19ab6740115ff7d1ae1615386e07b9e27e61975bfa6a2c2c946a1ced8d93875`
Status: `REJECTED_FIRST_PASS_SPARSE_PF_LEAD_LOST`

## Verdict

Reject v0 without tuning.

This candidate passed the focused unit test, measured-cost structural precheck with caution, hypothesis registration, and research smoke. The H1 execution layer did not solve the H4 BTC+GVZ sparse lead. Capital.com remained profitable, but Pepperstone and Dukascopy were negative across costs, no cell reached the 40-trade minimum, and max zero-trade months still reached 11.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Total PnL USD | Losing months % | Max zero months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 11 | 54.55% | 1.5633 | 107.07 | 2.78% | 11 |
| 2 | capital_com | median | 11 | 54.55% | 1.5633 | 107.07 | 2.78% | 11 |
| 3 | capital_com | p95 | 11 | 54.55% | 1.5032 | 96.88 | 2.78% | 11 |
| 4 | pepperstone | best_case | 20 | 45.00% | 0.9747 | -11.90 | 19.44% | 6 |
| 5 | pepperstone | median | 20 | 45.00% | 0.9747 | -11.90 | 19.44% | 6 |
| 6 | pepperstone | p95 | 20 | 45.00% | 0.9471 | -25.02 | 19.44% | 6 |
| 7 | dukascopy | best_case | 25 | 52.00% | 0.9508 | -23.96 | 16.67% | 11 |
| 8 | dukascopy | median | 25 | 52.00% | 0.8673 | -66.22 | 16.67% | 11 |
| 9 | dukascopy | p95 | 25 | 52.00% | 0.8229 | -87.00 | 16.67% | 11 |

## Gate Snapshot

| Gate | Result |
| --- | --- |
| Measured-cost structural precheck | PASS_WITH_COST_CAUTION, median stop 300 points, P95 cost_R 0.2500 |
| Focused unit test | PASS |
| Research candidate smoke | PASS, 1 synthetic signal |
| PF >= 1.30 in at least 7/9 cells | FAIL, 3/9 |
| At least 40 trades per cell | FAIL, 0/9 |
| Positive PnL persistence | FAIL, 3/9 and Capital.com-only |
| Max zero-trade months <= 3 | FAIL, max 11 |
| Cross-broker persistence | FAIL, Pepperstone and Dukascopy negative |
| Concentration | FAIL, top-trade concentration remains extreme |

## Interpretation

The H1 execution retest did not preserve the two-broker PF pocket from `h4_btc_gvz_dual_vol_reversal_v0`. It slightly increased Dukascopy and Pepperstone trade counts versus the H4 branch, but not enough to pass sample-size gates, and it diluted expectancy below PF 1.0 outside Capital.com.

Do not tune v0. The BTC+GVZ clue remains H4-sparse only; this H1 version is not a path to an approval-worthy EA.

## Evidence

- Hypothesis: `docs/hypothesis_h1_btc_gvz_dual_vol_reversal_v0.md`
- Cost precheck: `PASS_WITH_COST_CAUTION`, median stop 300 points, P95 cost_R 0.2500
- Registration: `outputs/reports/h1_btc_gvz_dual_vol_reversal_v0_research_hypothesis_registration.md`
- Smoke: `outputs/reports/h1_btc_gvz_dual_vol_reversal_v0_research_smoke.md`
- Matrix: `outputs/matrix_results/h1_btc_gvz_dual_vol_reversal_v0/`
