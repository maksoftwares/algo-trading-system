# A3 ML Dukascopy M5 Momentum Portability V1

Classification: `DUKASCOPY_M5_MOMENTUM_PORTABILITY_NO_SURVIVOR`

Historical cross-feed research only. No demo or broker action is authorized.

## Population

- M5 bars: `425311`
- Raw candidates: `2842`
- Raw resolved: `2807` (100.00%)
- Selected executable trades: `120`

## Evidence

| Window | Trades | Trades/source day | Trades/active day | Coverage | Win rate | Net USD | PF | Avg R | DD USD | Positive months |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| prehistory | 75 | 0.073 | 1.172 | 6.20% | 48.00% | -85.97 | 0.6677 | -0.2514 | 111.24 | 13/32 |
| replication | 45 | 0.087 | 1.286 | 6.80% | 73.33% | 68.23 | 1.6751 | 0.2118 | 32.28 | 12/15 |

## Quality Gates

- `verified_h1_months_eq_expected`: PASS
- `verified_m5_months_eq_expected`: PASS
- `raw_candidates_ge_minimum`: PASS
- `resolved_share_ge_minimum`: PASS
- `selected_timeout_share_lte_maximum`: PASS
- `candidate_ids_unique`: PASS
- `selected_candidate_ids_unique`: PASS
- `ea_source_hash_matches`: PASS
- `portfolio_spec_hash_matches`: PASS
- `all_lanes_represented`: PASS

## Strategy Gates

- `prehistory_rows_ge_minimum`: FAIL
- `replication_rows_ge_minimum`: FAIL
- `each_window_trades_per_source_day_ge_minimum`: FAIL
- `each_window_trades_per_active_day_ge_minimum`: FAIL
- `each_window_active_day_coverage_ge_minimum`: FAIL
- `prehistory_win_rate_ge_minimum`: FAIL
- `replication_win_rate_ge_minimum`: PASS
- `prehistory_pf_ge_minimum`: FAIL
- `replication_pf_ge_minimum`: PASS
- `each_window_positive_month_share_ge_minimum`: FAIL
- `prehistory_drawdown_usd_lte_maximum`: PASS
- `replication_drawdown_usd_lte_maximum`: PASS
- `concurrent_trades_lte_maximum`: PASS
- `each_lane_net_nonnegative_each_window`: FAIL
- `top25_removed_net_positive_each_window`: FAIL
- `bootstrap_p025_above_zero_each_window`: FAIL

Strategy promotion, demo prediction, EA consumption, and broker action remain disabled.
