# V60 Executable ML Top-Up V1 Result

Decision: **HISTORICAL_OR_EXECUTION_GATES_FAIL_KEEP_ML_OFF_DEMO**

Historical development research only. No runtime or broker authorization is granted.

## Causality And Behavior

- Current V60 population: 2069 rows.
- Incomplete M5 bars used: 0.
- Known-risk model-training population: 1625 rows.
- Proposed / accepted top-ups: 174 / 135.
- Baseline trades skipped: 0.

## Full Walk-Forward

| policy | trades | net | PF | win rate | closed DD | floating DD | net/floating DD | delta years >= 0 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| V60 baseline | 1676 | $5045.67 | 1.721 | 45.58% | $298.06 | $335.34 | 15.05 | 6/6 |
| Primary source-aware ML | 1676 | $5047.13 | 1.681 | 45.58% | $337.91 | $383.77 | 13.15 | 4/6 |

Primary delta: **$1.46**. Weekly-block one-sided 95% lower bound: **$-136.47**.

## Recent Window

Window: 2025-07-01 through 2026-06-30, grouped by entry time.

| policy | trades | net | PF | win rate | closed DD | floating DD |
|---|---:|---:|---:|---:|---:|---:|
| V60 baseline | 356 | $2502.72 | 1.984 | 44.10% | $152.89 | $258.70 |
| Primary source-aware ML | 356 | $2527.87 | 1.978 | 44.10% | $152.89 | $258.70 |

## Gates

- Passed: **14/20**.
- PASS: `all_features_available_at_entry`.
- PASS: `training_used_no_missing_risk`.
- PASS: `topups_used_no_missing_risk`.
- PASS: `no_baseline_trade_skipped`.
- PASS: `net_pnl_not_below_baseline`.
- FAIL: `profit_factor_not_below_baseline`.
- FAIL: `floating_drawdown_not_above_baseline`.
- FAIL: `net_to_floating_drawdown_improves_at_least_5pct`.
- PASS: `green_month_within_2_points`.
- FAIL: `at_least_5_of_6_delta_years_nonnegative`.
- FAIL: `weekly_block_bootstrap_lower_bound_above_zero`.
- PASS: `recent_net_pnl_not_below_baseline`.
- FAIL: `recent_profit_factor_not_below_baseline`.
- PASS: `recent_closed_drawdown_not_above_baseline`.
- PASS: `minimum_4_of_5_seeds_nonnegative`.
- PASS: `lot_values_broker_expressible`.
- PASS: `account_risk_limit_respected`.
- PASS: `directional_risk_limit_respected`.
- PASS: `addon_risk_limit_respected`.
- PASS: `position_limits_respected`.

## Demo Verdict

Do not connect this ML candidate to demo shadow or orders. Keep deterministic V60 unchanged.
