# Phase 0 Rejected Candidate Gate Audit

Generated at UTC: `2026-05-28T15:09:56+00:00`

Purpose: answer Review #3 V3 by aggregating the matrix gates that rejected candidate experts.

Approved/same-family rows are included for context but excluded from the rejection counts.

Approved or active experts excluded from rejection counts: `breakout_retest, swing_breakout_retest_v0, symbol_normalized_round_retest_v0`

## Summary

- Audited candidates: 67
- Rejected/research candidates audited: 64
- Rejected candidates with sample-size failure: 14
- Rejected candidates with multi-cell expectancy failure: 62
- Rejected candidates with both expectancy and sample-size failure: 14
- Rejected candidates with expectancy-only failure: 48
- Rejected candidates with frequency-only failure: 0

Conclusion: Sample-size/frequency failures are present, so low-frequency candidates should not be rescued by assumption; however, expectancy survival failures are at least as common and must remain the primary rejection evidence.

## Candidate Gate Table

| Candidate | Scope | Diagnosis | Cells | PF cells | Trades | Min trades | Failed gates |
|---|---|---|---:|---:|---:|---:|---|
| breakout_retest | APPROVED_OR_ACTIVE | APPROVED_EDGE_FAMILY | 9 | 7 | 66759 | 7174 | none |
| swing_breakout_retest_v0 | APPROVED_OR_ACTIVE | APPROVED_EDGE_FAMILY | 9 | 7 | 57897 | 6281 | none |
| symbol_normalized_round_retest_v0 | APPROVED_OR_ACTIVE | APPROVED_EDGE_FAMILY | 9 | 9 | 47388 | 3837 | none |
| asia_range_london_breakout_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 4845 | 507 | multi_cell_survival;no_catastrophic_failure;concentration |
| asia_range_london_failed_break_reversal_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 3102 | 326 | multi_cell_survival;no_catastrophic_failure;concentration |
| compression_retest_continuation_v0 | REJECTED_OR_RESEARCH | EDGE_AND_FREQUENCY_FAILURE | 9 | 0 | 0 | 0 | multi_cell_survival;sample_size;concentration;activity;cost_sensitivity |
| cot_gold_positioning_reversal_v0 | REJECTED_OR_RESEARCH | EDGE_AND_FREQUENCY_FAILURE | 9 | 0 | 126 | 5 | multi_cell_survival;sample_size;concentration;activity |
| d1_compression_h4_expansion_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 783 | 68 | multi_cell_survival;concentration |
| d1_inside_day_breakout_v0 | REJECTED_OR_RESEARCH | EDGE_AND_FREQUENCY_FAILURE | 9 | 3 | 192 | 11 | multi_cell_survival;sample_size;concentration;activity |
| d1_momentum_h4_pullback_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 3 | 684 | 69 | multi_cell_survival;concentration |
| d1_multi_day_exhaustion_reversion_v0 | REJECTED_OR_RESEARCH | EDGE_AND_FREQUENCY_FAILURE | 9 | 0 | 291 | 24 | multi_cell_survival;sample_size;concentration;activity |
| d1_outside_day_followthrough_v0 | REJECTED_OR_RESEARCH | EDGE_AND_FREQUENCY_FAILURE | 9 | 0 | 261 | 22 | multi_cell_survival;sample_size;concentration;activity |
| d1_volatility_expansion_reversal_v0 | REJECTED_OR_RESEARCH | EDGE_AND_FREQUENCY_FAILURE | 9 | 0 | 354 | 30 | multi_cell_survival;sample_size;concentration |
| d1_w1_momentum_h4_pullback_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 3 | 552 | 53 | multi_cell_survival;concentration |
| daily_pivot_reclaim_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 4713 | 486 | multi_cell_survival;no_catastrophic_failure;concentration |
| emr_inactivity_long_v0 | REJECTED_OR_RESEARCH | EDGE_AND_FREQUENCY_FAILURE | 9 | 0 | 84 | 9 | multi_cell_survival;sample_size;concentration;activity |
| extreme_activity_mean_reversion_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 1056 | 74 | multi_cell_survival;concentration |
| gold_fx_proxy_divergence_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 1044 | 99 | multi_cell_survival;concentration |
| h1_calendar_drift_state_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 8661 | 802 | multi_cell_survival;no_catastrophic_failure;concentration |
| h1_m5_path_skew_reversal_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 4920 | 498 | multi_cell_survival;concentration |
| h1_macro_event_aftershock_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 810 | 85 | multi_cell_survival;concentration |
| h1_return_autocorrelation_state_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 1497 | 148 | multi_cell_survival;concentration |
| h1_smooth_trend_exhaustion_reversal_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 486 | 42 | multi_cell_survival;concentration |
| h1_tick_volume_climax_reversal_v0 | REJECTED_OR_RESEARCH | EDGE_AND_FREQUENCY_FAILURE | 9 | 0 | 2904 | 0 | multi_cell_survival;sample_size;no_catastrophic_failure;concentration;activity;cost_sensitivity |
| h1_volatility_squeeze_breakout_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 3 | 2127 | 116 | multi_cell_survival;concentration |
| h1_walk_forward_linear_state_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 5979 | 561 | multi_cell_survival;concentration |
| h4_breakeven_inflation_momentum_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 2055 | 183 | multi_cell_survival;concentration |
| h4_credit_spread_stress_momentum_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 1689 | 153 | multi_cell_survival;concentration;activity |
| h4_d1_momentum_expansion_continuation_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 3 | 735 | 81 | multi_cell_survival;concentration |
| h4_financial_conditions_stress_reversal_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 483 | 46 | multi_cell_survival;concentration;activity |
| h4_gold_futures_volume_climax_v0 | REJECTED_OR_RESEARCH | EDGE_AND_FREQUENCY_FAILURE | 9 | 0 | 141 | 11 | multi_cell_survival;sample_size;concentration;activity |
| h4_gvz_volatility_panic_reversal_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 489 | 48 | multi_cell_survival;concentration;activity |
| h4_inside_bar_d1_momentum_breakout_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 2 | 741 | 71 | multi_cell_survival;concentration |
| h4_macro_composite_risk_state_v0 | REJECTED_OR_RESEARCH | EDGE_AND_FREQUENCY_FAILURE | 9 | 6 | 516 | 34 | multi_cell_survival;sample_size;concentration;activity |
| h4_macro_composite_risk_state_v1 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 3 | 894 | 51 | multi_cell_survival;concentration;activity |
| h4_policy_uncertainty_safe_haven_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 3 | 1443 | 142 | multi_cell_survival;concentration |
| h4_real_yield_proxy_momentum_v0 | REJECTED_OR_RESEARCH | EDGE_AND_FREQUENCY_FAILURE | 9 | 3 | 306 | 18 | multi_cell_survival;sample_size;concentration;activity |
| h4_treasury_curve_stress_momentum_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 3 | 975 | 55 | multi_cell_survival;concentration;activity |
| h4_us_session_liquidity_reversal_v0 | REJECTED_OR_RESEARCH | EDGE_AND_FREQUENCY_FAILURE | 9 | 0 | 378 | 32 | multi_cell_survival;sample_size;concentration |
| h4_vix_risk_off_reversal_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 3 | 504 | 47 | multi_cell_survival;concentration |
| h4_walk_forward_knn_momentum_state_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 5013 | 485 | multi_cell_survival;concentration;activity |
| liquidity_sweep_continuation_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 12222 | 1281 | multi_cell_survival;no_catastrophic_failure;concentration |
| liquidity_sweep_reversal_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 3906 | 393 | multi_cell_survival;no_catastrophic_failure;concentration |
| london_fix_continuation_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 4821 | 463 | multi_cell_survival;concentration |
| m15_inside_bar_breakout_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 7170 | 727 | multi_cell_survival;concentration |
| m15_two_bar_exhaustion_reversal_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 12282 | 1304 | multi_cell_survival;no_catastrophic_failure;concentration |
| m15_two_bar_impulse_continuation_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 11191 | 1192 | multi_cell_survival;no_catastrophic_failure;concentration |
| m5_impulse_continuation_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 20346 | 2199 | multi_cell_survival;no_catastrophic_failure;concentration |
| ny_am_pullback_continuation_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 3195 | 326 | multi_cell_survival;concentration |
| ny_failed_london_reversal_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 3369 | 322 | multi_cell_survival;concentration |
| ny_london_overlap_compression_break_v0 | REJECTED_OR_RESEARCH | EDGE_AND_FREQUENCY_FAILURE | 9 | 3 | 135 | 2 | multi_cell_survival;sample_size;concentration;activity;cost_sensitivity |
| opening_drive_failed_continuation_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 2208 | 221 | multi_cell_survival;concentration |
| post_spike_short_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 1860 | 192 | multi_cell_survival;concentration |
| previous_day_extreme_retest_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 5295 | 478 | multi_cell_survival;no_catastrophic_failure;concentration |
| range_mr | REJECTED_OR_RESEARCH | EDGE_AND_FREQUENCY_FAILURE | 9 | 0 | 24 | 0 | multi_cell_survival;sample_size;concentration;activity;cost_sensitivity |
| round_number_retest_v0 | REJECTED_OR_RESEARCH | NON_MATRIX_REJECTION_OR_PENDING | 9 | 9 | 47388 | 3837 | none |
| session_extreme_retest_v0 | REJECTED_OR_RESEARCH | NON_MATRIX_REJECTION_OR_PENDING | 9 | 9 | 23727 | 2331 | none |
| session_vwap_reclaim_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 4806 | 481 | multi_cell_survival;no_catastrophic_failure;concentration |
| squeeze_breakout_long_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 1800 | 194 | multi_cell_survival;concentration |
| symbol_round_sweep_reversal_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 9609 | 685 | multi_cell_survival;no_catastrophic_failure;concentration |
| trend_pullback | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 27576 | 2873 | multi_cell_survival;no_catastrophic_failure;concentration |
| w1_d1_momentum_continuation_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 3 | 498 | 48 | multi_cell_survival;concentration |
| weekly_level_reclaim_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 1083 | 113 | multi_cell_survival;concentration |
| weekly_open_reversion_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 1878 | 197 | multi_cell_survival;no_catastrophic_failure;concentration |
| xag_lead_xau_followthrough_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 7608 | 816 | multi_cell_survival;concentration |
| xau_xag_fx_composite_reversion_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 4704 | 506 | multi_cell_survival;concentration |
| xau_xag_relative_value_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 936 | 102 | multi_cell_survival;concentration |

## Gate Columns

- `multi_cell_survival`: PF persistence across the 9-cell matrix.
- `sample_size`: minimum trades in every cell.
- `no_catastrophic_failure`: drawdown and total-return loss limits.
- `concentration`: single/top-5 trade contribution limits.
- `activity`: zero-trade month limit.
- `cost_sensitivity`: P95 PF divided by best-case PF.
