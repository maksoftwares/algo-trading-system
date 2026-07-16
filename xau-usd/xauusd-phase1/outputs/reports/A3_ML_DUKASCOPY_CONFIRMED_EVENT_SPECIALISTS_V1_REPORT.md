# A3 ML Dukascopy Confirmed Event Specialists V1

Classification: `NO_TRAIN_FAMILY_SURVIVOR`

## Source And Quality

- Source months: `120`
- M5 feature rows: `708538`
- Candidates: `149`
- Resolved share: `100.00%`
- Quality `all_expected_months_valid`: `True`
- Quality `resolved_share_ge_minimum`: `True`
- Quality `candidate_ids_unique`: `True`
- Quality `candidate_keys_unique`: `True`
- Quality `candidates_chronological`: `True`
- Quality `h1_source_reconciles`: `True`

## Family Firewall

### session_boundary_sweep_reclaim_v1

- train: opened `True`, passed `False`, trades `3`, PF `0.000`, average R `-1.1107`, net R `-3.33`
- validation: opened `False`, passed `False`, trades `5`, PF `0.309`, average R `-0.6160`, net R `-3.08`
- internal_test: opened `False`, passed `False`, trades `4`, PF `0.408`, average R `-0.4943`, net R `-1.98`
- exam: opened `False`, passed `False`, trades `19`, PF `0.478`, average R `-0.4162`, net R `-7.91`

### compression_break_retest_v1

- train: opened `True`, passed `False`, trades `0`, PF `n/a`, average R `0.0000`, net R `0.00`
- validation: opened `False`, passed `False`, trades `0`, PF `n/a`, average R `0.0000`, net R `0.00`
- internal_test: opened `False`, passed `False`, trades `0`, PF `n/a`, average R `0.0000`, net R `0.00`
- exam: opened `False`, passed `False`, trades `0`, PF `n/a`, average R `0.0000`, net R `0.00`

### shock_failure_reclaim_v1

- train: opened `True`, passed `False`, trades `15`, PF `0.201`, average R `-0.7943`, net R `-11.91`
- validation: opened `False`, passed `False`, trades `28`, PF `0.738`, average R `-0.1665`, net R `-4.66`
- internal_test: opened `False`, passed `False`, trades `37`, PF `0.400`, average R `-0.4521`, net R `-16.73`
- exam: opened `False`, passed `False`, trades `30`, PF `1.054`, average R `0.0320`, net R `0.96`

## Survivor Portfolio

- Exam survivors: `[]`
- Exam trades: `0`
- Exam trades/source day: `0.000`
- Exam stress PF: `n/a`
- Exam average stress R: `0.0000`
- Exam closed drawdown R: `0.00`
- Portfolio gate `trades_per_source_day_ge_minimum`: `False`
- Portfolio gate `pf_ge_minimum`: `False`
- Portfolio gate `average_r_ge_minimum`: `False`
- Portfolio gate `drawdown_r_lte_maximum`: `True`
- Portfolio gate `top_episode_share_lte_maximum`: `True`
- Portfolio gate `top_three_episodes_removed_positive`: `False`

## Authorization

- Research only: `true`
- Forward shadow candidate: `False`
- Demo or live authorized: `false`
