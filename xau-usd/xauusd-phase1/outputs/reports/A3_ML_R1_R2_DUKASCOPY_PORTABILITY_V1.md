# A3 ML R1/R2 Dukascopy Portability V1

Classification: `PORTABILITY_FAIL`

Cross-feed research only. Demo prediction, EA consumption, and broker action remain disabled.

## Evidence

| Window | Scope | Trades | Stress net | PF | Win rate | Closed DD |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| historical_backcast | portfolio | 801 | 1714.38 | 1.2944 | 39.95% | 1131.39 |
| historical_backcast | r1_box_clean_strict_uptrend | 196 | 1572.96 | 1.4988 | 48.47% | 934.64 |
| historical_backcast | r2_pullback_short_h1_confirm | 605 | 141.42 | 1.0530 | 37.19% | 362.52 |
| recent_cross_feed | portfolio | 135 | 8613.25 | 4.0574 | 60.00% | 701.79 |
| recent_cross_feed | r1_box_clean_strict_uptrend | 114 | 8547.74 | 4.2492 | 64.91% | 701.79 |
| recent_cross_feed | r2_pullback_short_h1_confirm | 21 | 65.51 | 1.3514 | 33.33% | 90.32 |

## Gates

- `source_months_eq_120`: PASS
- `candidate_ids_unique`: PASS
- `all_selected_entries_not_before_decision`: PASS
- `all_selected_resolved`: PASS
- `portfolio_stress_pf_each_window`: PASS
- `specialist_stress_pf_each_window`: PASS
- `specialist_stress_net_positive_each_window`: PASS
- `drawdown_to_net_each_window`: FAIL
- `positive_calendar_year_share`: PASS
- `positive_six_month_block_share`: PASS
- `episode_concentration`: FAIL
- `top_three_episodes_removed_net_positive`: FAIL
- `reference_count_ratio`: PASS
- `reference_timestamp_delta`: FAIL

No demo or broker authorization was changed.
