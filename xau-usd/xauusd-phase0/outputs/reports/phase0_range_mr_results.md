# Phase 0 Results: Range Mr

Generated at UTC: 2026-05-21T12:07:48+00:00

## Hypothesis

| Field | Value |
| --- | --- |
| Hypothesis file name | docs/hypothesis_range_mr.md |
| Registered SHA256 | f99de28b321cd2e7b530db6e7bc0ad4d016003ad0e32fdaad311ed97ff019274 |
| Current SHA256 | f99de28b321cd2e7b530db6e7bc0ad4d016003ad0e32fdaad311ed97ff019274 |
| Hash match | yes |

## 9-Cell Matrix Results

| cell_id | tick_source | cost_model | trade_count | profit_factor | total_return_pct | max_drawdown_pct | max_consecutive_zero_trade_months | p95_to_best_pf_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | capital_com | best_case | 3 | 0 | -1.487 | 1.487 | 33 |  |
| 2 | capital_com | median | 3 | 0 | -1.487 | 1.487 | 33 |  |
| 3 | capital_com | p95 | 3 | 0 | -1.583 | 1.583 | 33 | 0 |
| 4 | pepperstone | best_case | 5 | 0 | -2.465 | 2.465 | 13 |  |
| 5 | pepperstone | median | 5 | 0 | -2.465 | 2.465 | 13 |  |
| 6 | pepperstone | p95 | 5 | 0 | -2.558 | 2.558 | 13 | 0 |
| 7 | dukascopy | best_case | 0 | 0 | 0 | 0 | 36 |  |
| 8 | dukascopy | median | 0 | 0 | 0 | 0 | 36 |  |
| 9 | dukascopy | p95 | 0 | 0 | 0 | 0 | 36 | 0 |

## Gate Pass/Fail Summary

| name | status | threshold | observed | message |
| --- | --- | --- | --- | --- |
| multi_cell_survival | FAIL | >=7/9 cells PF >= 1.3 | 0/9 cells PF >= 1.3 | Too few profitable cells. |
| sample_size | FAIL | trade_count >= 40 in every cell | failed cells: 1, 2, 3, 4, 5, 6, 7, 8, 9 | One or more cells have too few trades. |
| no_catastrophic_failure | PASS | max_drawdown_pct <= 30.0; total_return_pct >= -25.0 | all cells meet threshold | Catastrophic-failure gate passed. |
| concentration | FAIL | largest <= 10.0%; top5 <= 40.0% | failed cells: 1, 2, 3, 4, 5, 6, 7, 8, 9 | Profit is too concentrated. |
| activity | FAIL | max_consecutive_zero_trade_months <= 3 | failed cells: 1, 2, 3, 4, 5, 6, 7, 8, 9 | One or more cells are inactive too long. |
| cost_sensitivity | FAIL | p95_pf / best_case_pf >= 0.5 for pairs 1/3, 4/6, 7/9 | 1/3=0; 4/6=0; 7/9=0 | Failed pairs: pair 1/3, pair 4/6, pair 7/9. |

## Decile Test

| name | status | threshold | observed | message |
| --- | --- | --- | --- | --- |
| decile_persistence | FAIL | >=8 deciles PF>1.0; no PF>2.0x median; each decile trades>=10 | positive_deciles=0, median_pf=0 | median PF 0.0 <= 0; 0 deciles PF > 1.0, need 8; one or more deciles below 10 trades |

| decile_id | trade_count | profit_factor | verdict |
| --- | --- | --- | --- |
| 1 | 0 | 0 | FAIL |
| 2 | 0 | 0 | FAIL |
| 3 | 2 | 0 | FAIL |
| 4 | 4 | 0 | FAIL |
| 5 | 3 | 0 | FAIL |
| 6 | 3 | 0 | FAIL |
| 7 | 3 | 0 | FAIL |
| 8 | 2 | 0 | FAIL |
| 9 | 3 | 0 | FAIL |
| 10 | 3 | 0 | FAIL |

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
| multi_symbol_consistency | FAIL | EURUSD PF >= 0.9 and USDJPY PF >= 0.9 | EURUSD=0, USDJPY=0 | Failed or missing symbols: EURUSD, USDJPY. |

| symbol | trade_count | profit_factor | verdict |
| --- | --- | --- | --- |
| EURUSD | 27 | 0 | FAIL |
| USDJPY | 16 | 0 | FAIL |

## Hypothesis vs Reality

| Claim | Hypothesis | Observed | Status |
| --- | --- | --- | --- |
| Trade count | 20 to 200 trades on XAUUSD M5, because strict low-ADX and range-touch filters should reduce activity. | 24 trades across 9 matrix cells | OBSERVED |
| Cost-adjusted PF | 1.05 to 1.40 across accepted matrix cells; at least 7 of 9 cells should meet PF >= 1.30 for approval. | median PF 0; min PF 0 | OBSERVED |
| Losing-month percentage | 25% to 55%. | worst cell 13.89% | OBSERVED |
| Worst single month | not worse than -12% starting equity under configured risk. | $-104.8 | OBSERVED |
| Max consecutive zero months | 0 to 3. | 36 | OBSERVED |
| R-multiple distribution | fewer trades than the other candidates, with stop-loss losses near -1R and occasional wider mean-reversion wins when the opposite boundary is reached. | avg R median -0.9958; median R median -0.9956 | OBSERVED |

## Ten-Gate Detail

| Gate | Name | Status | Threshold | Observed |
| --- | --- | --- | --- | --- |
| Gate 1 | Multi-cell survival | FAIL | >=7/9 cells PF >= 1.3 | 0/9 cells PF >= 1.3 |
| Gate 2 | Sample size | FAIL | trade_count >= 40 in every cell | failed cells: 1, 2, 3, 4, 5, 6, 7, 8, 9 |
| Gate 3 | No catastrophic failure | PASS | max_drawdown_pct <= 30.0; total_return_pct >= -25.0 | all cells meet threshold |
| Gate 4 | Concentration | FAIL | largest <= 10.0%; top5 <= 40.0% | failed cells: 1, 2, 3, 4, 5, 6, 7, 8, 9 |
| Gate 5 | Activity | FAIL | max_consecutive_zero_trade_months <= 3 | failed cells: 1, 2, 3, 4, 5, 6, 7, 8, 9 |
| Gate 6 | Cost sensitivity | FAIL | p95_pf / best_case_pf >= 0.5 for pairs 1/3, 4/6, 7/9 | 1/3=0; 4/6=0; 7/9=0 |
| Gate 7 | Decile persistence | FAIL | >=8 deciles PF>1.0; no PF>2.0x median; each decile trades>=10 | positive_deciles=0, median_pf=0 |
| Gate 8 | Multi-symbol consistency | FAIL | EURUSD PF >= 0.9 and USDJPY PF >= 0.9 | EURUSD=0, USDJPY=0 |
| Gate 9 | Adversarial review | PENDING | logic_gap_failures_pct <= 25.0 | manual review incomplete |
| Gate 10 | Hypothesis SHA256 lock | PASS | current SHA256 equals registered SHA256 | hash match |

## Final Verdict

| 9-cell | Decile | Adversarial | Multi-symbol | Hypothesis-match | FINAL |
| --- | --- | --- | --- | --- | --- |
| FAIL | FAIL | PENDING | FAIL | PASS | FAIL |

## Failed Gates

- 9-cell:multi_cell_survival - Too few profitable cells.
- 9-cell:sample_size - One or more cells have too few trades.
- 9-cell:concentration - Profit is too concentrated.
- 9-cell:activity - One or more cells are inactive too long.
- 9-cell:cost_sensitivity - Failed pairs: pair 1/3, pair 4/6, pair 7/9.
- Decile:decile_persistence - median PF 0.0 <= 0; 0 deciles PF > 1.0, need 8; one or more deciles below 10 trades
- Multi-symbol:multi_symbol_consistency - Failed or missing symbols: EURUSD, USDJPY.

## Passing Evidence

- 9-cell:no_catastrophic_failure - all cells meet threshold
- Hypothesis SHA256 matches the registered manifest.
