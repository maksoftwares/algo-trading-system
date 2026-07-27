# V6 Causal ML Expected Value V2 Result

Decision: **V6_CAUSAL_ML_EXPECTED_VALUE_V2_HISTORICAL_GATE_FAIL_QUARANTINED**

Historical research only. Execution is not authorized.

## Selection

- Frozen nominations: 277
- Selected nominations: 29
- Accepted beside V60: 24

## V6 Comparison

- Raw V6 net/PF/DD: $303.59 / 1.178 / $298.34
- V2 V6 net/PF/DD: $-161.25 / 0.593 / $203.00

## Shared Account

- V60 net/PF/DD: $5458.39 / 1.649 / $298.06
- V60 plus V2 net/PF/DD: $5297.14 / 1.602 / $320.42
- Floating drawdown: $336.78

## Annual Models

```csv
target_year,training_rows,training_last_exit_time,training_target_mean,training_target_std,target_rows,target_selected_rows,target_retained_share,target_auc,target_spearman,target_score_mean,target_score_min,target_score_max
2022,64277,2021-12-29 15:00:00+00:00,-0.3391,1.3672,61,3,0.0492,0.5455,0.1460,-0.1969,-0.4394,0.0975
2023,76070,2022-12-29 20:00:00+00:00,-0.3236,1.3704,60,2,0.0333,0.6177,0.3734,-0.2222,-0.4059,0.1637
2024,87861,2023-12-29 20:55:00+00:00,-0.3140,1.3757,65,0,0.0000,0.4648,-0.0090,-0.2185,-0.5055,-0.0463
2025,99613,2024-12-29 22:25:00+00:00,-0.3007,1.3799,55,12,0.2182,0.4769,-0.1409,-0.1501,-0.3720,0.1762
2026,111311,2025-12-29 13:40:00+00:00,-0.2815,1.3872,36,12,0.3333,0.4984,-0.1985,-0.1946,-0.6093,0.2567
```

## Required Windows

```csv
window,v60_trades,v60_win_rate_pct,v60_stress_net_usd,v60_stress_profit_factor,v60_stress_closed_drawdown_usd,v60_winner_removed_stress_net_usd,raw_v6_trades,raw_v6_win_rate_pct,raw_v6_stress_net_usd,raw_v6_stress_profit_factor,raw_v6_stress_closed_drawdown_usd,raw_v6_winner_removed_stress_net_usd,ml_v6_trades,ml_v6_win_rate_pct,ml_v6_stress_net_usd,ml_v6_stress_profit_factor,ml_v6_stress_closed_drawdown_usd,ml_v6_winner_removed_stress_net_usd,raw_combined_trades,raw_combined_win_rate_pct,raw_combined_stress_net_usd,raw_combined_stress_profit_factor,raw_combined_stress_closed_drawdown_usd,raw_combined_winner_removed_stress_net_usd,ml_combined_trades,ml_combined_win_rate_pct,ml_combined_stress_net_usd,ml_combined_stress_profit_factor,ml_combined_stress_closed_drawdown_usd,ml_combined_winner_removed_stress_net_usd,passed
development_2,595,47.059,1044.317,1.584,248.027,739.167,112,31.250,66.705,1.107,162.246,-158.572,2,50.000,-4.775,0.507,9.691,0.000,707,44.554,1111.022,1.460,264.973,805.872,597,47.069,1039.542,1.578,252.802,734.392,False
confirmation,441,46.032,1223.652,1.621,298.064,662.012,43,41.860,87.429,1.283,76.401,-137.518,5,20.000,-63.980,0.010,64.600,0.000,484,45.661,1311.081,1.575,345.541,749.441,446,45.740,1159.672,1.570,298.064,598.032,False
final,364,43.956,2509.445,1.960,152.889,1116.732,33,33.333,103.853,1.165,298.339,-466.303,14,28.571,-68.868,0.763,136.622,-273.596,397,43.073,2613.298,1.806,230.115,1220.585,378,43.386,2440.577,1.840,168.164,1047.865,False
```

## Interpretation

This exact expected-value model is quarantined because it did not improve V6 and V60 across every locked quality and risk gate. It must not be deployed or tuned in place.
