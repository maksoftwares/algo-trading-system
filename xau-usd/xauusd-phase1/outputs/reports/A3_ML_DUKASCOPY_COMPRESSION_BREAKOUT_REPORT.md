# A3 ML Dukascopy D1 Compression H4 Breakout V1

Classification: `DUKASCOPY_COMPRESSION_BREAKOUT_INVALID`

Historical Dukascopy research only. No demo or broker action is authorized.

## Population

- Candidates: `31`
- Eligible candidates: `31`
- Resolved: `31` (100.00%)

## Chronological Evidence

| Split | Trades | Win rate | Stress net USD | Stress PF | Average stress R | Max DD R | Positive months |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| train | 14 | 35.71% | -18.10 | 0.9129 | -0.0633 | 4.94 | 2/7 |
| validation | 14 | 35.71% | 2.00 | 1.0111 | -0.0349 | 4.16 | 2/9 |
| test | 3 | 33.33% | -6.34 | 0.8590 | -0.0705 | 1.13 | 1/3 |

## Quality Gates

- `verified_months_eq_expected`: PASS
- `candidates_ge_minimum`: FAIL
- `resolved_share_ge_minimum`: PASS
- `each_split_rows_ge_minimum`: FAIL
- `each_direction_rows_ge_minimum`: FAIL
- `candidate_ids_unique`: PASS
- `candidate_keys_unique`: PASS

## Strategy Gates

- `train_pf_ge_minimum`: FAIL
- `validation_pf_ge_minimum`: FAIL
- `test_pf_ge_minimum`: FAIL
- `train_average_r_ge_minimum`: FAIL
- `validation_average_r_ge_minimum`: FAIL
- `test_average_r_ge_minimum`: FAIL
- `test_drawdown_r_lte_maximum`: PASS
- `validation_positive_month_share_ge_minimum`: FAIL
- `test_positive_month_share_ge_minimum`: FAIL
- `test_each_direction_rows_ge_minimum`: FAIL
- `test_average_r_bootstrap_p025_above_zero`: FAIL

Test month-bootstrap average-R interval: `None` to `None`.

Strategy promotion, demo prediction, EA consumption, and broker action remain disabled.
