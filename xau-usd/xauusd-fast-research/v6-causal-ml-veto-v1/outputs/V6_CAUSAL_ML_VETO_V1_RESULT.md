# V6 Causal ML Veto V1 Result

Decision: **V6_CAUSAL_ML_VETO_HISTORICAL_GATE_FAIL_QUARANTINED**

Historical research only. Execution is not authorized.

## Veto Behavior

- Frozen V6 nominations: 277
- ML-selected nominations: 209
- Accepted beside V60: 177
- Winning trades retained: 79.2%
- Rejected trades that were losses: 69.1%

## Shared Account

- V60 stress net: $5458.39
- V60 plus ML stress net: $5752.38
- V60 PF: 1.649
- V60 plus ML PF: 1.591
- V60 closed drawdown: $298.06
- V60 plus ML closed drawdown: $324.57
- V60 floating drawdown: $335.34
- V60 plus ML floating drawdown: $401.99

## Annual Models

```csv
target_year,training_rows,training_last_exit_time,calibration_rows,calibration_start_time,calibration_last_exit_time,calibration_auc,calibration_brier,probability_cutoff,target_rows,target_selected_rows,target_retained_share,target_auc,target_brier
2022,52546,2020-12-29 15:30:00+00:00,11600,2021-01-03 23:05:00+00:00,2021-12-29 15:00:00+00:00,0.5214,0.2057,0.2782,61,58,0.9508,0.6154,0.2273
2023,64277,2021-12-29 15:00:00+00:00,11662,2022-01-02 23:05:00+00:00,2022-12-29 20:00:00+00:00,0.5782,0.2108,0.2822,60,37,0.6167,0.5714,0.2048
2024,76070,2022-12-29 20:00:00+00:00,11701,2023-01-02 23:05:00+00:00,2023-12-29 20:55:00+00:00,0.5586,0.2076,0.2823,65,51,0.7846,0.5424,0.2274
2025,87861,2023-12-29 20:55:00+00:00,11715,2024-01-02 01:10:00+00:00,2024-12-29 22:25:00+00:00,0.5739,0.2144,0.3110,55,50,0.9091,0.4918,0.2483
2026,99613,2024-12-29 22:25:00+00:00,11590,2025-01-02 01:10:00+00:00,2025-12-29 13:40:00+00:00,0.5381,0.2207,0.3243,36,13,0.3611,0.4921,0.2526
```

## Required Windows

```csv
window,v60_trades,v60_win_rate_pct,v60_stress_net_usd,v60_stress_profit_factor,v60_stress_closed_drawdown_usd,v60_winner_removed_stress_net_usd,raw_v6_trades,raw_v6_win_rate_pct,raw_v6_stress_net_usd,raw_v6_stress_profit_factor,raw_v6_stress_closed_drawdown_usd,raw_v6_winner_removed_stress_net_usd,ml_v6_trades,ml_v6_win_rate_pct,ml_v6_stress_net_usd,ml_v6_stress_profit_factor,ml_v6_stress_closed_drawdown_usd,ml_v6_winner_removed_stress_net_usd,raw_combined_trades,raw_combined_win_rate_pct,raw_combined_stress_net_usd,raw_combined_stress_profit_factor,raw_combined_stress_closed_drawdown_usd,raw_combined_winner_removed_stress_net_usd,ml_combined_trades,ml_combined_win_rate_pct,ml_combined_stress_net_usd,ml_combined_stress_profit_factor,ml_combined_stress_closed_drawdown_usd,ml_combined_winner_removed_stress_net_usd,passed
development_2,595,47.059,1044.317,1.584,248.027,739.167,112,31.250,66.705,1.107,162.246,-158.572,92,34.783,85.904,1.165,90.155,-111.955,707,44.554,1111.022,1.460,264.973,805.872,687,45.415,1130.221,1.489,234.628,825.071,False
confirmation,441,46.032,1223.652,1.621,298.064,662.012,43,41.860,87.429,1.283,76.401,-137.518,38,47.368,126.568,1.488,71.281,-98.380,484,45.661,1311.081,1.575,345.541,749.441,479,46.138,1350.220,1.605,324.572,788.580,False
final,364,43.956,2509.445,1.960,152.889,1116.732,33,33.333,103.853,1.165,298.339,-466.303,23,30.435,31.054,1.077,185.239,-347.490,397,43.073,2613.298,1.806,230.115,1220.585,387,43.152,2540.499,1.841,191.876,1147.786,False
```

## Interpretation

This exact ML veto is quarantined because it did not improve the frozen V6/V60 system across every preregistered quality and risk gate. It must not be deployed or tuned in place.
