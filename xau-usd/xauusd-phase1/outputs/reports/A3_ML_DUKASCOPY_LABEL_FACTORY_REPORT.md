# A3 ML Dukascopy Candidate-Label Factory V1

Classification: `DUKASCOPY_LABEL_DATASET_READY_FAMILY_NO_SURVIVOR`

This is historical research based on verified Dukascopy bid/ask data. It does not authorize demo or live trading.

## Dataset

- Verified months: `72`
- Candidates: `3340`
- Entry-window eligible candidates: `3263`
- Entry-window ineligible candidates: `77`
- Resolved eligible labels: `3261` (99.94%)
- Minority label share: `33.30%`

## Chronological Evidence

| Split | Trades | Win rate | Stress net USD | Stress PF | Avg stress R | Max closed DD R |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| train | 1488 | 33.87% | -1618.30 | 0.8160 | -0.1100 | 175.46 |
| validation | 1206 | 31.59% | -1356.45 | 0.8147 | -0.1528 | 206.21 |
| test | 567 | 35.45% | -145.32 | 0.9569 | -0.0658 | 88.93 |

## Dataset Quality Gates

- `verified_months_eq_expected`: PASS
- `total_candidates_ge_minimum`: PASS
- `resolved_share_ge_minimum`: PASS
- `each_split_rows_ge_minimum`: PASS
- `each_direction_rows_ge_minimum`: PASS
- `minority_label_share_ge_minimum`: PASS
- `candidate_ids_unique`: PASS
- `candidate_keys_unique`: PASS
- `all_resolved_entries_at_or_after_decision`: PASS

## Strategy Research Gates

- `train_stress_pf_ge_minimum`: FAIL
- `validation_stress_pf_ge_minimum`: FAIL
- `test_stress_pf_ge_minimum`: FAIL
- `validation_average_stress_r_ge_minimum`: FAIL
- `test_average_stress_r_ge_minimum`: FAIL
- `test_closed_drawdown_r_lte_maximum`: FAIL

## Decision Boundary

- ML training authorized by label quality: `True`
- Candidate-family promotion: `false`
- Python demo predictions: `false`
- EA or broker action: `false`
