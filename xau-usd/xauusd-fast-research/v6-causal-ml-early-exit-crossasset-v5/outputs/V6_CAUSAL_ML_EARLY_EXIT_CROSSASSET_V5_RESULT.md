# V6 Causal ML Early Exit Cross-Asset V5 Result

Decision: **V6_CAUSAL_ML_EARLY_EXIT_CROSSASSET_V5_HISTORICAL_GATE_FAIL_QUARANTINED**

Historical research only. Execution is not authorized.

## Cross-Asset Coverage

- DXY 1h: 97.7%
- Treasury 1h: 96.2%
- Common dollar 1h: 100.0%

## Utility Actions

- Frozen V1 selected nominations: 209
- V5 early exits: 54
- Early-exit share: 25.8%
- Positive-benefit precision: 68.5%
- Realized pre-routing benefit: $-252.84
- Worst early-exit benefit: $-75.34

## V6 Sleeve

- Frozen V1 net / PF / DD: $293.99 / 1.221 / $199.12
- Cross-asset V5 net / PF / DD: $100.01 / 1.082 / $253.30

## Shared Account

- Frozen V1 combined net / PF / closed DD / floating DD: $5752.38 / 1.591 / $324.57 / $401.99
- Cross-asset V5 combined net / PF / closed DD / floating DD: $5558.40 / 1.578 / $336.19 / $413.60

## V4 Comparison

- V4 actions / benefit: 54 / $-245.37
- V4 V6 net / PF / DD: $102.96 / 1.084 / $269.96

## Annual Models

```csv
target_year,training_rows,training_last_original_exit_time,training_target_mean_r,training_target_q25_r,target_rows,target_spearman,target_pinball_loss,target_score_mean_r,target_score_max_r,first_action_trades,first_action_positive_benefit_share,first_action_net_benefit_usd,first_action_worst_benefit_usd
2022,230109,2021-12-29 15:00:00+00:00,0.0232,-0.5948,200,0.1081,0.5374,-0.6518,0.5095,14,0.7857,2.8574,-15.5928
2023,272299,2022-12-29 20:00:00+00:00,0.0193,-0.6245,123,-0.1586,0.6239,-0.6983,0.4900,11,0.7273,-23.9292,-25.7564
2024,314249,2023-12-29 20:55:00+00:00,0.0131,-0.6337,153,-0.0566,0.7184,-0.7073,0.4552,14,0.5714,-73.7796,-30.1580
2025,356284,2024-12-29 22:25:00+00:00,0.0069,-0.6502,164,0.0237,0.8590,-0.7236,0.4750,13,0.6923,-115.4527,-75.3356
2026,399359,2025-12-29 13:40:00+00:00,-0.0008,-0.6776,47,0.3380,1.0247,-0.7091,0.3631,2,0.5000,-42.5394,-60.5216
```

## Required Windows

```csv
window,v1_v6_trades,v1_v6_win_rate_pct,v1_v6_stress_net_usd,v1_v6_stress_profit_factor,v1_v6_stress_closed_drawdown_usd,v1_v6_winner_removed_stress_net_usd,managed_v6_trades,managed_v6_win_rate_pct,managed_v6_stress_net_usd,managed_v6_stress_profit_factor,managed_v6_stress_closed_drawdown_usd,managed_v6_winner_removed_stress_net_usd,v1_combined_trades,v1_combined_win_rate_pct,v1_combined_stress_net_usd,v1_combined_stress_profit_factor,v1_combined_stress_closed_drawdown_usd,v1_combined_winner_removed_stress_net_usd,managed_combined_trades,managed_combined_win_rate_pct,managed_combined_stress_net_usd,managed_combined_stress_profit_factor,managed_combined_stress_closed_drawdown_usd,managed_combined_winner_removed_stress_net_usd,passed
development_2,92,34.783,85.904,1.165,90.155,-111.955,89,30.337,61.306,1.133,92.655,-136.553,687,45.415,1130.221,1.489,234.628,825.071,684,44.883,1105.623,1.491,272.290,800.473,False
confirmation,38,47.368,126.568,1.488,71.281,-98.380,38,34.211,25.459,1.099,92.718,-175.625,479,46.138,1350.220,1.605,324.572,788.580,479,45.094,1249.111,1.561,336.188,687.471,False
final,23,30.435,31.054,1.077,185.239,-347.490,23,21.739,-13.850,0.960,218.247,-344.929,387,43.152,2540.499,1.841,191.876,1147.786,387,42.636,2495.595,1.843,202.261,1102.882,False
```

## Failed Checks

minimum_years_positive_first_action_net, minimum_first_action_positive_benefit_share, minimum_total_first_action_benefit_usd, maximum_early_exit_trade_share, all_required_windows_pass, managed_v6_net_no_worse_than_v1, managed_v6_pf_no_worse_than_v1, managed_v6_closed_drawdown_no_worse_than_v1, managed_combined_net_no_worse_than_v1, managed_combined_pf_no_worse_than_v1, managed_combined_closed_drawdown_no_worse_than_v1, managed_combined_floating_drawdown_no_worse_than_v1

## Interpretation

The locked cross-asset feature addition failed one or more coverage, model, economic, window, or drawdown gates. This exact V5 is quarantined and cannot be deployed or tuned in place.
