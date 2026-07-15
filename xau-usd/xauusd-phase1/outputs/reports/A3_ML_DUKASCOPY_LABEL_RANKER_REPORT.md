# A3 ML Dukascopy Label Ranker V1

Classification: `DUKASCOPY_LABEL_RANKER_NO_SURVIVOR`

Offline historical research only. No demo or broker action is authorized.

## Model

- Validation AUC: `0.457698`
- Test AUC: `0.503956`
- Frozen validation cutoff: `0.36999987`

## Selected Subsets

| Split | Selected | Coverage | Stress PF | Average stress R | Stress net USD | Max DD R | Positive months |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Validation | 302 | 25.04% | 0.6834 | -0.2213 | -625.36 | 78.31 | 6/24 |
| Test | 205 | 36.16% | 0.9749 | -0.0528 | -31.50 | 26.01 | 5/12 |

Test month-bootstrap 95% interval for average stress R: `-0.3707` to `0.3018`.

## Gates

- `validation_auc_ge_minimum`: FAIL
- `test_auc_ge_minimum`: FAIL
- `validation_selected_rows_ge_minimum`: PASS
- `test_selected_rows_ge_minimum`: PASS
- `test_each_direction_rows_ge_minimum`: PASS
- `validation_selected_pf_ge_minimum`: FAIL
- `test_selected_pf_ge_minimum`: FAIL
- `validation_selected_average_r_ge_minimum`: FAIL
- `test_selected_average_r_ge_minimum`: FAIL
- `test_selected_drawdown_r_lte_maximum`: FAIL
- `test_coverage_inside_bounds`: PASS
- `validation_positive_month_share_ge_minimum`: FAIL
- `test_positive_month_share_ge_minimum`: FAIL
- `test_average_r_bootstrap_p025_above_zero`: FAIL
- `validation_brier_better_than_train_prior`: FAIL
- `test_brier_better_than_train_prior`: FAIL

Candidate-family promotion, demo prediction, EA consumption, and broker action remain disabled.
