# V6 Causal ML Early Exit V3 Result

Decision: **V6_CAUSAL_ML_EARLY_EXIT_V3_HISTORICAL_GATE_FAIL_QUARANTINED**

Historical research only. Execution is not authorized.

## Management Behavior

- Frozen V1 selected nominations: 209
- Early exits before routing: 77
- Early-exit share: 36.8%
- Trigger precision: 68.8%
- Accepted managed trades: 173
- Net dollars saved before routing: $-299.44

## V6 Sleeve

- Frozen V1 net / PF / DD: $293.99 / 1.221 / $199.12
- Managed V3 net / PF / DD: $116.29 / 1.101 / $271.92

## Shared Account

- Frozen V1 combined net / PF / closed DD / floating DD: $5752.38 / 1.591 / $324.57 / $401.99
- Managed V3 combined net / PF / closed DD / floating DD: $5574.68 / 1.583 / $336.19 / $413.60

## Annual Model Audit

```csv
target_year,training_rows,training_positive_share,training_last_original_exit_time,target_rows,target_positive_share,target_auc,target_brier,triggered_snapshots,trigger_precision
2022,230109,0.6391,2021-12-29 15:00:00+00:00,200,0.4900,0.7352,0.2188,41,0.8293
2023,272299,0.6354,2022-12-29 20:00:00+00:00,123,0.6098,0.6469,0.2221,28,0.8214
2024,314249,0.6340,2023-12-29 20:55:00+00:00,153,0.4379,0.6090,0.2586,35,0.6857
2025,356284,0.6309,2024-12-29 22:25:00+00:00,164,0.4878,0.5935,0.2516,30,0.5000
2026,399359,0.6283,2025-12-29 13:40:00+00:00,47,0.4894,0.8062,0.2156,6,0.6667
```

## Required Windows

```csv
window,v1_v6_trades,v1_v6_win_rate_pct,v1_v6_stress_net_usd,v1_v6_stress_profit_factor,v1_v6_stress_closed_drawdown_usd,v1_v6_winner_removed_stress_net_usd,managed_v6_trades,managed_v6_win_rate_pct,managed_v6_stress_net_usd,managed_v6_stress_profit_factor,managed_v6_stress_closed_drawdown_usd,managed_v6_winner_removed_stress_net_usd,v1_combined_trades,v1_combined_win_rate_pct,v1_combined_stress_net_usd,v1_combined_stress_profit_factor,v1_combined_stress_closed_drawdown_usd,v1_combined_winner_removed_stress_net_usd,managed_combined_trades,managed_combined_win_rate_pct,managed_combined_stress_net_usd,managed_combined_stress_profit_factor,managed_combined_stress_closed_drawdown_usd,managed_combined_winner_removed_stress_net_usd,passed
development_2,92,34.783,85.904,1.165,90.155,-111.955,88,28.409,100.712,1.246,70.599,-97.147,687,45.415,1130.221,1.489,234.628,825.071,683,44.656,1145.029,1.521,260.115,839.879,False
confirmation,38,47.368,126.568,1.488,71.281,-98.380,38,31.579,33.636,1.136,93.055,-167.448,479,46.138,1350.220,1.605,324.572,788.580,479,44.885,1257.288,1.566,336.188,695.648,False
final,23,30.435,31.054,1.077,185.239,-347.490,23,17.391,-34.295,0.901,252.979,-347.709,387,43.152,2540.499,1.841,191.876,1147.786,387,42.377,2475.151,1.836,202.261,1082.438,False
```

## Interpretation

This exact post-entry classifier is quarantined because it did not improve every preregistered discrimination, P&L, drawdown, window, and shared-risk gate. It must not be deployed or tuned in place.
