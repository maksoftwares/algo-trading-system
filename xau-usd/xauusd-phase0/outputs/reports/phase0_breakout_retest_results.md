# Phase 0 Results: Breakout Retest

Generated at UTC: 2026-05-21T12:07:48+00:00

## Hypothesis

| Field | Value |
| --- | --- |
| Hypothesis file name | docs/hypothesis_breakout_retest.md |
| Registered SHA256 | 4532100fdd87a21179ff78da45c6be4edc15a93a7a5baafad0c31683fe991206 |
| Current SHA256 | 4532100fdd87a21179ff78da45c6be4edc15a93a7a5baafad0c31683fe991206 |
| Hash match | yes |

## 9-Cell Matrix Results

| cell_id | tick_source | cost_model | trade_count | profit_factor | total_return_pct | max_drawdown_pct | max_consecutive_zero_trade_months | p95_to_best_pf_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | capital_com | best_case | 7287 | 1.412 | 1.864e+05 | 9.813 | 0 |  |
| 2 | capital_com | median | 7287 | 1.412 | 1.864e+05 | 9.813 | 0 |  |
| 3 | capital_com | p95 | 7287 | 1.255 | 1.739e+04 | 11.12 | 0 | 0.8889 |
| 4 | pepperstone | best_case | 7174 | 1.306 | 5.062e+04 | 17.86 | 0 |  |
| 5 | pepperstone | median | 7174 | 1.306 | 5.062e+04 | 17.86 | 0 |  |
| 6 | pepperstone | p95 | 7174 | 1.233 | 1.006e+04 | 20.89 | 0 | 0.9446 |
| 7 | dukascopy | best_case | 7792 | 1.514 | 7.316e+05 | 10.97 | 0 |  |
| 8 | dukascopy | median | 7792 | 1.514 | 7.315e+05 | 10.97 | 0 |  |
| 9 | dukascopy | p95 | 7792 | 1.399 | 7.413e+04 | 12.49 | 0 | 0.924 |

## Gate Pass/Fail Summary

| name | status | threshold | observed | message |
| --- | --- | --- | --- | --- |
| multi_cell_survival | PASS | >=7/9 cells PF >= 1.3 | 7/9 cells PF >= 1.3 | Multi-cell survival passed. |
| sample_size | PASS | trade_count >= 40 in every cell | all cells meet threshold | Sample-size gate passed. |
| no_catastrophic_failure | PASS | max_drawdown_pct <= 30.0; total_return_pct >= -25.0 | all cells meet threshold | Catastrophic-failure gate passed. |
| concentration | PASS | largest <= 10.0%; top5 <= 40.0% | all cells meet threshold | Concentration gate passed. |
| activity | PASS | max_consecutive_zero_trade_months <= 3 | all cells meet threshold | Activity gate passed. |
| cost_sensitivity | PASS | p95_pf / best_case_pf >= 0.5 for pairs 1/3, 4/6, 7/9 | 1/3=0.8889; 4/6=0.9446; 7/9=0.924 | Cost-sensitivity gate passed. |

## Decile Test

| name | status | threshold | observed | message |
| --- | --- | --- | --- | --- |
| decile_persistence | PASS | >=8 deciles PF>1.0; no PF>2.0x median; each decile trades>=10 | positive_deciles=10, median_pf=1.441 | Decile persistence passed. |

| decile_id | trade_count | profit_factor | verdict |
| --- | --- | --- | --- |
| 1 | 2251 | 1.468 | PASS |
| 2 | 2296 | 1.305 | PASS |
| 3 | 2338 | 1.421 | PASS |
| 4 | 2303 | 1.474 | PASS |
| 5 | 2362 | 1.3 | PASS |
| 6 | 2258 | 1.456 | PASS |
| 7 | 2391 | 1.334 | PASS |
| 8 | 2161 | 1.426 | PASS |
| 9 | 2390 | 1.532 | PASS |
| 10 | 2405 | 1.605 | PASS |

## Adversarial Search

| name | status | threshold | observed | message |
| --- | --- | --- | --- | --- |
| adversarial_review | PASS | logic_gap_failures_pct <= 25.0 | logic_gap_failures_pct=0.0 | Adversarial gate passed. |

| reviewed_losing_trades | logic_gap_failures | logic_gap_failures_pct |
| --- | --- | --- |
| 120 | 0 | 0 |

## Multi-Symbol Check

| name | status | threshold | observed | message |
| --- | --- | --- | --- | --- |
| multi_symbol_consistency | PASS | EURUSD PF >= 0.9 and USDJPY PF >= 0.9 | EURUSD=1.451, USDJPY=1.54 | EURUSD and USDJPY passed directionality threshold. |

| symbol | trade_count | profit_factor | verdict |
| --- | --- | --- | --- |
| EURUSD | 26515 | 1.451 | PASS |
| USDJPY | 25384 | 1.54 | PASS |

## Hypothesis vs Reality

| Claim | Hypothesis | Observed | Status |
| --- | --- | --- | --- |
| Trade count | 1800 to 3200 trades on XAUUSD M5, depending on broker coverage and cost model. | 66759 trades across 9 matrix cells | OBSERVED |
| Cost-adjusted PF | 1.20 to 1.60 across accepted matrix cells; at least 7 of 9 cells should meet PF >= 1.30. | median PF 1.399; min PF 1.233 | OBSERVED |
| Losing-month percentage | 10% to 35%. | worst cell 11.11% | OBSERVED |
| Worst single month | not worse than -15% starting equity under configured risk. | $-3062 | OBSERVED |
| Max consecutive zero months | 0 to 1. | 0 | OBSERVED |
| R-multiple distribution | median losing trade near -1R, frequent small losses, and a right tail from 1.5R target hits; average R should remain positive after costs. | avg R median 0.1776; median R median -0.9901 | OBSERVED |

## Ten-Gate Detail

| Gate | Name | Status | Threshold | Observed |
| --- | --- | --- | --- | --- |
| Gate 1 | Multi-cell survival | PASS | >=7/9 cells PF >= 1.3 | 7/9 cells PF >= 1.3 |
| Gate 2 | Sample size | PASS | trade_count >= 40 in every cell | all cells meet threshold |
| Gate 3 | No catastrophic failure | PASS | max_drawdown_pct <= 30.0; total_return_pct >= -25.0 | all cells meet threshold |
| Gate 4 | Concentration | PASS | largest <= 10.0%; top5 <= 40.0% | all cells meet threshold |
| Gate 5 | Activity | PASS | max_consecutive_zero_trade_months <= 3 | all cells meet threshold |
| Gate 6 | Cost sensitivity | PASS | p95_pf / best_case_pf >= 0.5 for pairs 1/3, 4/6, 7/9 | 1/3=0.8889; 4/6=0.9446; 7/9=0.924 |
| Gate 7 | Decile persistence | PASS | >=8 deciles PF>1.0; no PF>2.0x median; each decile trades>=10 | positive_deciles=10, median_pf=1.441 |
| Gate 8 | Multi-symbol consistency | PASS | EURUSD PF >= 0.9 and USDJPY PF >= 0.9 | EURUSD=1.451, USDJPY=1.54 |
| Gate 9 | Adversarial review | PASS | logic_gap_failures_pct <= 25.0 | logic_gap_failures_pct=0.0 |
| Gate 10 | Hypothesis SHA256 lock | PASS | current SHA256 equals registered SHA256 | hash match |

## Final Verdict

| 9-cell | Decile | Adversarial | Multi-symbol | Hypothesis-match | FINAL |
| --- | --- | --- | --- | --- | --- |
| PASS | PASS | PASS | PASS | PASS | PASS |

## Failed Gates

None.

## Passing Evidence

- 9-cell:multi_cell_survival - 7/9 cells PF >= 1.3
- 9-cell:sample_size - all cells meet threshold
- 9-cell:no_catastrophic_failure - all cells meet threshold
- 9-cell:concentration - all cells meet threshold
- 9-cell:activity - all cells meet threshold
- 9-cell:cost_sensitivity - 1/3=0.8889; 4/6=0.9446; 7/9=0.924
- Decile:decile_persistence - positive_deciles=10, median_pf=1.441
- Adversarial:adversarial_review - logic_gap_failures_pct=0.0
- Multi-symbol:multi_symbol_consistency - EURUSD=1.451, USDJPY=1.54
- Hypothesis SHA256 matches the registered manifest.
