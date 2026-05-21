# Phase 0 Results: Trend Pullback

Generated at UTC: 2026-05-21T12:07:48+00:00

## Hypothesis

| Field | Value |
| --- | --- |
| Hypothesis file name | docs/hypothesis_trend_pullback.md |
| Registered SHA256 | b99448c11f462a6e8397666e16c429e5ded73a86281a42cbe9bce17807086d1d |
| Current SHA256 | b99448c11f462a6e8397666e16c429e5ded73a86281a42cbe9bce17807086d1d |
| Hash match | yes |

## 9-Cell Matrix Results

| cell_id | tick_source | cost_model | trade_count | profit_factor | total_return_pct | max_drawdown_pct | max_consecutive_zero_trade_months | p95_to_best_pf_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | capital_com | best_case | 3280 | 0.8038 | -80.9 | 81.79 | 0 |  |
| 2 | capital_com | median | 3280 | 0.8038 | -80.9 | 81.79 | 0 |  |
| 3 | capital_com | p95 | 3280 | 0.7493 | -88.67 | 89.1 | 0 | 0.9322 |
| 4 | pepperstone | best_case | 2873 | 0.9364 | -44.53 | 51.9 | 0 |  |
| 5 | pepperstone | median | 2873 | 0.9364 | -44.53 | 51.9 | 0 |  |
| 6 | pepperstone | p95 | 2873 | 0.8909 | -62.73 | 64.86 | 0 | 0.9514 |
| 7 | dukascopy | best_case | 3039 | 1.007 | 6.98 | 27.08 | 0 |  |
| 8 | dukascopy | median | 3039 | 0.9606 | -31.89 | 44.48 | 0 |  |
| 9 | dukascopy | p95 | 3039 | 0.8665 | -72.13 | 73.98 | 0 | 0.8606 |

## Gate Pass/Fail Summary

| name | status | threshold | observed | message |
| --- | --- | --- | --- | --- |
| multi_cell_survival | FAIL | >=7/9 cells PF >= 1.3 | 0/9 cells PF >= 1.3 | Too few profitable cells. |
| sample_size | PASS | trade_count >= 40 in every cell | all cells meet threshold | Sample-size gate passed. |
| no_catastrophic_failure | FAIL | max_drawdown_pct <= 30.0; total_return_pct >= -25.0 | failed cells: 1, 2, 3, 4, 5, 6, 8, 9 | One or more cells breached loss limits. |
| concentration | FAIL | largest <= 10.0%; top5 <= 40.0% | failed cells: 1, 2, 3, 4, 5, 6, 7, 8, 9 | Profit is too concentrated. |
| activity | PASS | max_consecutive_zero_trade_months <= 3 | all cells meet threshold | Activity gate passed. |
| cost_sensitivity | PASS | p95_pf / best_case_pf >= 0.5 for pairs 1/3, 4/6, 7/9 | 1/3=0.9322; 4/6=0.9514; 7/9=0.8606 | Cost-sensitivity gate passed. |

## Decile Test

| name | status | threshold | observed | message |
| --- | --- | --- | --- | --- |
| decile_persistence | FAIL | >=8 deciles PF>1.0; no PF>2.0x median; each decile trades>=10 | positive_deciles=1, median_pf=0.9008 | 1 deciles PF > 1.0, need 8 |

| decile_id | trade_count | profit_factor | verdict |
| --- | --- | --- | --- |
| 1 | 1064 | 0.7664 | FAIL |
| 2 | 989 | 0.8734 | FAIL |
| 3 | 979 | 0.8003 | FAIL |
| 4 | 839 | 0.8489 | FAIL |
| 5 | 930 | 0.8716 | FAIL |
| 6 | 929 | 0.9514 | FAIL |
| 7 | 913 | 0.9288 | FAIL |
| 8 | 954 | 0.9289 | FAIL |
| 9 | 938 | 1.023 | PASS |
| 10 | 968 | 0.9283 | FAIL |

## Adversarial Search

| name | status | threshold | observed | message |
| --- | --- | --- | --- | --- |
| adversarial_review | PENDING | logic_gap_failures_pct <= 25.0 | manual review incomplete | Manual adversarial review is incomplete. |

| reviewed_losing_trades | logic_gap_failures | logic_gap_failures_pct |
| --- | --- | --- |
| 0 | 0 | 0 |

## Multi-Symbol Check

| name | status | threshold | observed | message |
| --- | --- | --- | --- | --- |
| multi_symbol_consistency | FAIL | EURUSD PF >= 0.9 and USDJPY PF >= 0.9 | EURUSD=0.8886, USDJPY=0.9292 | Failed or missing symbols: EURUSD. |

| symbol | trade_count | profit_factor | verdict |
| --- | --- | --- | --- |
| EURUSD | 10021 | 0.8886 | FAIL |
| USDJPY | 3610 | 0.9292 | PASS |

## Hypothesis vs Reality

| Claim | Hypothesis | Observed | Status |
| --- | --- | --- | --- |
| Trade count | 800 to 2500 trades on XAUUSD M5, depending on broker coverage and trend persistence. | 27576 trades across 9 matrix cells | OBSERVED |
| Cost-adjusted PF | 1.15 to 1.45 across accepted matrix cells; at least 7 of 9 cells should meet PF >= 1.30 for approval. | median PF 0.8909; min PF 0.7493 | OBSERVED |
| Losing-month percentage | 20% to 45%. | worst cell 91.67% | OBSERVED |
| Worst single month | not worse than -18% starting equity under configured risk. | $-1286 | OBSERVED |
| Max consecutive zero months | 0 to 2. | 0 | OBSERVED |
| R-multiple distribution | many small stop-loss outcomes near -1R, clustered around pullback failures, balanced by 1.5R trend-continuation winners; average R should be positive in passing cells. | avg R median -0.06555; median R median -0.9373 | OBSERVED |

## Ten-Gate Detail

| Gate | Name | Status | Threshold | Observed |
| --- | --- | --- | --- | --- |
| Gate 1 | Multi-cell survival | FAIL | >=7/9 cells PF >= 1.3 | 0/9 cells PF >= 1.3 |
| Gate 2 | Sample size | PASS | trade_count >= 40 in every cell | all cells meet threshold |
| Gate 3 | No catastrophic failure | FAIL | max_drawdown_pct <= 30.0; total_return_pct >= -25.0 | failed cells: 1, 2, 3, 4, 5, 6, 8, 9 |
| Gate 4 | Concentration | FAIL | largest <= 10.0%; top5 <= 40.0% | failed cells: 1, 2, 3, 4, 5, 6, 7, 8, 9 |
| Gate 5 | Activity | PASS | max_consecutive_zero_trade_months <= 3 | all cells meet threshold |
| Gate 6 | Cost sensitivity | PASS | p95_pf / best_case_pf >= 0.5 for pairs 1/3, 4/6, 7/9 | 1/3=0.9322; 4/6=0.9514; 7/9=0.8606 |
| Gate 7 | Decile persistence | FAIL | >=8 deciles PF>1.0; no PF>2.0x median; each decile trades>=10 | positive_deciles=1, median_pf=0.9008 |
| Gate 8 | Multi-symbol consistency | FAIL | EURUSD PF >= 0.9 and USDJPY PF >= 0.9 | EURUSD=0.8886, USDJPY=0.9292 |
| Gate 9 | Adversarial review | PENDING | logic_gap_failures_pct <= 25.0 | manual review incomplete |
| Gate 10 | Hypothesis SHA256 lock | PASS | current SHA256 equals registered SHA256 | hash match |

## Final Verdict

| 9-cell | Decile | Adversarial | Multi-symbol | Hypothesis-match | FINAL |
| --- | --- | --- | --- | --- | --- |
| FAIL | FAIL | PENDING | FAIL | PASS | FAIL |

## Failed Gates

- 9-cell:multi_cell_survival - Too few profitable cells.
- 9-cell:no_catastrophic_failure - One or more cells breached loss limits.
- 9-cell:concentration - Profit is too concentrated.
- Decile:decile_persistence - 1 deciles PF > 1.0, need 8
- Multi-symbol:multi_symbol_consistency - Failed or missing symbols: EURUSD.

## Passing Evidence

- 9-cell:sample_size - all cells meet threshold
- 9-cell:activity - all cells meet threshold
- 9-cell:cost_sensitivity - 1/3=0.9322; 4/6=0.9514; 7/9=0.8606
- Hypothesis SHA256 matches the registered manifest.
