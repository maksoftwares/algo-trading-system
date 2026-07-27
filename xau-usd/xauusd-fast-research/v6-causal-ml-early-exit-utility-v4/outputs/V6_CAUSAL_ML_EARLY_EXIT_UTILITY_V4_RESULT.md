# V6 Causal ML Early Exit Utility V4 Result

Decision: **V6_CAUSAL_ML_EARLY_EXIT_UTILITY_V4_HISTORICAL_GATE_FAIL_QUARANTINED**

Historical research only. Execution is not authorized.

## Utility Actions

- Frozen V1 selected nominations: 209
- V4 early exits: 54
- Early-exit share: 25.8%
- Positive-benefit precision: 70.4%
- Realized pre-routing benefit: $-245.37
- Worst early-exit benefit: $-75.34

## V6 Sleeve

- Frozen V1 net / PF / DD: $293.99 / 1.221 / $199.12
- Utility V4 net / PF / DD: $102.96 / 1.084 / $269.96

## Shared Account

- Frozen V1 combined net / PF / closed DD / floating DD: $5752.38 / 1.591 / $324.57 / $401.99
- Utility V4 combined net / PF / closed DD / floating DD: $5561.35 / 1.578 / $336.19 / $413.60

## Annual Models

```csv
target_year,training_rows,training_last_original_exit_time,training_target_mean_r,training_target_q25_r,target_rows,target_spearman,target_pinball_loss,target_score_mean_r,target_score_max_r,first_action_trades,first_action_positive_benefit_share,first_action_net_benefit_usd,first_action_worst_benefit_usd
2022,230109,2021-12-29 15:00:00+00:00,0.0232,-0.5948,200,0.1181,0.5375,-0.6323,0.5241,14,0.7857,3.9866,-15.5928
2023,272299,2022-12-29 20:00:00+00:00,0.0193,-0.6245,123,-0.1625,0.6310,-0.6724,0.4969,13,0.7692,-12.6007,-25.7564
2024,314249,2023-12-29 20:55:00+00:00,0.0131,-0.6337,153,-0.0479,0.7204,-0.6821,0.4475,13,0.6154,-57.3329,-30.1580
2025,356284,2024-12-29 22:25:00+00:00,0.0069,-0.6502,164,0.0088,0.8552,-0.7385,0.5219,12,0.6667,-136.8797,-75.3356
2026,399359,2025-12-29 13:40:00+00:00,-0.0008,-0.6776,47,0.3627,1.0183,-0.7000,0.3843,2,0.5000,-42.5394,-60.5216
```

## Required Windows

```csv
window,v1_v6_trades,v1_v6_win_rate_pct,v1_v6_stress_net_usd,v1_v6_stress_profit_factor,v1_v6_stress_closed_drawdown_usd,v1_v6_winner_removed_stress_net_usd,managed_v6_trades,managed_v6_win_rate_pct,managed_v6_stress_net_usd,managed_v6_stress_profit_factor,managed_v6_stress_closed_drawdown_usd,managed_v6_winner_removed_stress_net_usd,v1_combined_trades,v1_combined_win_rate_pct,v1_combined_stress_net_usd,v1_combined_stress_profit_factor,v1_combined_stress_closed_drawdown_usd,v1_combined_winner_removed_stress_net_usd,managed_combined_trades,managed_combined_win_rate_pct,managed_combined_stress_net_usd,managed_combined_stress_profit_factor,managed_combined_stress_closed_drawdown_usd,managed_combined_winner_removed_stress_net_usd,passed
development_2,92,34.783,85.904,1.165,90.155,-111.955,89,31.461,85.680,1.191,85.857,-112.179,687,45.415,1130.221,1.489,234.628,825.071,684,45.029,1129.997,1.505,265.492,824.847,False
confirmation,38,47.368,126.568,1.488,71.281,-98.380,38,34.211,25.459,1.099,92.718,-175.625,479,46.138,1350.220,1.605,324.572,788.580,479,45.094,1249.111,1.561,336.188,687.471,False
final,23,30.435,31.054,1.077,185.239,-347.490,23,21.739,-35.277,0.904,239.674,-366.356,387,43.152,2540.499,1.841,191.876,1147.786,387,42.636,2474.168,1.830,202.261,1081.455,False
```

## Interpretation

The locked conservative utility policy failed one or more model, economic, window, or drawdown gates. This exact V4 is quarantined and cannot be deployed or tuned in place.
