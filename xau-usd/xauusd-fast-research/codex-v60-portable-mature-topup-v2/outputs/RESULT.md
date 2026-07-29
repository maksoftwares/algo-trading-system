# V60 Portable Mature Top-Up V2 Result

Decision: **HISTORICAL_PORTABILITY_GATES_PASS_PROSPECTIVE_DEMO_NOMINATION_ONLY**

| policy | trades | net | PF | win rate | closed DD | floating DD | net/floating DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| V60 baseline | 1676 | $5045.67 | 1.721 | 45.58% | $298.06 | $335.34 | 15.05 |
| Portable ML top-up | 1676 | $5296.78 | 1.723 | 45.58% | $297.84 | $329.35 | 16.08 |

- Delta: `$251.10`.
- Proposed / accepted top-ups: `271 / 82`.
- Top-up PF: `1.773`.
- Weekly-block lower 95% bound: `$92.38`.

## Gates

- PASS: `all_features_available_at_entry`.
- PASS: `feed_specific_features_excluded`.
- PASS: `every_baseline_trade_retained`.
- PASS: `no_missing_risk_topup`.
- PASS: `net_not_below_baseline`.
- PASS: `profit_factor_within_one_percent`.
- PASS: `floating_drawdown_not_above_baseline`.
- PASS: `net_to_floating_drawdown_improves_five_percent`.
- PASS: `all_mature_years_nonnegative`.
- PASS: `topup_profit_factor_at_least_1_2`.
- PASS: `weekly_block_lower_bound_above_zero`.
- PASS: `recent_net_not_below_baseline`.
- PASS: `at_least_four_seeds_positive`.
- PASS: `at_least_four_seeds_stable_by_year`.

Historical development evidence only. No runtime or broker authority is granted by this result.
