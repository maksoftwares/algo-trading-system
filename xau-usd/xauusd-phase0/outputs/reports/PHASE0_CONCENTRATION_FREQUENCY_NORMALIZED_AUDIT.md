# Phase 0 Frequency-Normalized Concentration Audit

Generated at UTC: `2026-05-27T09:35:59+00:00`

Overall status: PASS

Purpose: answer Review #6 by checking whether absolute concentration failures are amplified by low trade frequency.

This report does not approve, rescue, tune, or reclassify any rejected candidate. It is review context only.

## Method

- Absolute concentration remains the original Phase 0 gate.
- Normalized top-trade ratio = `top_trade_R / (mean_abs_R * sqrt(n_trades))`.
- Normalized top-5 ratio = `top5_trade_R_sum / (mean_abs_R * sqrt(n_trades))`.
- Review-context thresholds: top-trade <= 1.00, top-5 <= 2.50.

## Summary

- Audited candidates: 65
- Absolute concentration-failed candidates: 60
- Review-context candidates under normalized thresholds: 59
- Candidates with high normalized concentration: 0

Conclusion: concentration-failed candidates remain rejected under the current Phase 0 rules. Normalized flags should only inform future gate design for new pre-registered low-frequency hypotheses.

## Candidate Table

| Candidate | Scope | Abs Gate | Cells | Trades | Max Single % | Max Top5 % | Norm Top | Norm Top5 | Flag | Gate Context |
|---|---|---|---:|---:|---:|---:|---:|---:|---|---|
| breakout_retest | APPROVED_OR_ACTIVE | PASS | 9 | 66759 | 0.7566 | 3.7706 | 0.014596 | 0.072829 | NOT_ABSOLUTE_CONCENTRATION_FAIL | none |
| swing_breakout_retest_v0 | APPROVED_OR_ACTIVE | PASS | 9 | 57897 | 0.7609 | 3.7931 | 0.015577 | 0.077779 | NOT_ABSOLUTE_CONCENTRATION_FAIL | none |
| symbol_normalized_round_retest_v0 | APPROVED_OR_ACTIVE | PASS | 9 | 47388 | 0.7623 | 3.7948 | 0.019751 | 0.098656 | NOT_ABSOLUTE_CONCENTRATION_FAIL | none |
| asia_range_london_breakout_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 4845 | 100.0 | 100.0 | 0.068632 | 0.316397 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;no_catastrophic_failure;concentration |
| asia_range_london_failed_break_reversal_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 3102 | 100.0 | 100.0 | 0.075313 | 0.363652 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;no_catastrophic_failure;concentration |
| compression_retest_continuation_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 0 | 100.0 | 100.0 | 0.0 | 0.0 | NORMALIZATION_UNDEFINED_NO_TRADES | multi_cell_survival;sample_size;concentration;activity;cost_sensitivity |
| cot_gold_positioning_reversal_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 126 | 510.922 | 993.2456 | 0.61179 | 1.758605 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;sample_size;concentration;activity |
| d1_compression_h4_expansion_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 783 | 100.0 | 100.0 | 0.202561 | 0.976849 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;concentration |
| d1_inside_day_breakout_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 192 | 100.0 | 100.0 | 0.452674 | 1.504711 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;sample_size;concentration;activity |
| d1_momentum_h4_pullback_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 684 | 68.9427 | 148.749 | 0.91943 | 1.801944 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;concentration |
| d1_multi_day_exhaustion_reversion_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 291 | 100.0 | 169.4033 | 0.321023 | 1.517631 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;sample_size;concentration;activity |
| d1_outside_day_followthrough_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 261 | 100.0 | 100.0 | 0.31156 | 1.453205 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;sample_size;concentration;activity |
| d1_volatility_expansion_reversal_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 354 | 100.0 | 170.9 | 0.273805 | 1.333514 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;sample_size;concentration |
| d1_w1_momentum_h4_pullback_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 552 | 60.9924 | 201.5032 | 0.386344 | 1.225295 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;concentration |
| daily_pivot_reclaim_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 4713 | 100.0 | 100.0 | 0.066935 | 0.305054 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;no_catastrophic_failure;concentration |
| emr_inactivity_long_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 84 | 1306.4986 | 5105.6392 | 0.416545 | 1.695691 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;sample_size;concentration;activity |
| extreme_activity_mean_reversion_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 1056 | 100.0 | 100.0 | 0.151877 | 0.750729 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;concentration |
| gold_fx_proxy_divergence_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 1044 | 100.0 | 243.4894 | 0.179865 | 0.806486 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;concentration |
| h1_calendar_drift_state_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 8661 | 100.0 | 100.0 | 0.396239 | 0.706334 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;no_catastrophic_failure;concentration |
| h1_m5_path_skew_reversal_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 4920 | 100.0 | 100.0 | 0.30479 | 0.539155 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;concentration |
| h1_macro_event_aftershock_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 810 | 100.0 | 404.178 | 0.238853 | 0.778705 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;concentration |
| h1_return_autocorrelation_state_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 1497 | 100.0 | 100.0 | 0.254866 | 0.798369 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;concentration |
| h1_smooth_trend_exhaustion_reversal_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 486 | 100.0 | 100.0 | 0.202137 | 0.980795 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;concentration |
| h1_tick_volume_climax_reversal_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 2904 | 100.0 | 100.0 | 0.065098 | 0.314496 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;sample_size;no_catastrophic_failure;concentration;activity;cost_sensitivity |
| h1_volatility_squeeze_breakout_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 2127 | 100.0 | 100.0 | 0.171019 | 0.82588 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;concentration |
| h1_walk_forward_linear_state_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 5979 | 100.0 | 129.2628 | 0.230808 | 0.830408 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;concentration |
| h4_breakeven_inflation_momentum_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 2055 | 100.0 | 100.0 | 0.130137 | 0.594438 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;concentration |
| h4_credit_spread_stress_momentum_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 1689 | 100.0 | 274.6079 | 0.188391 | 0.780804 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;concentration;activity |
| h4_d1_momentum_expansion_continuation_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 735 | 100.0 | 111.7863 | 0.1678 | 0.809899 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;concentration |
| h4_financial_conditions_stress_reversal_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 483 | 100.0 | 100.0 | 0.356255 | 1.407623 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;concentration;activity |
| h4_gvz_volatility_panic_reversal_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 489 | 100.0 | 212.5005 | 0.277442 | 1.289932 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;concentration;activity |
| h4_inside_bar_d1_momentum_breakout_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 741 | 92.6435 | 446.3203 | 0.16605 | 0.808783 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;concentration |
| h4_macro_composite_risk_state_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 516 | 118.853 | 561.4902 | 0.268946 | 1.300981 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;sample_size;concentration;activity |
| h4_macro_composite_risk_state_v1 | REJECTED_OR_RESEARCH | FAIL | 9 | 894 | 100.0 | 100.0 | 0.22252 | 1.082554 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;concentration;activity |
| h4_policy_uncertainty_safe_haven_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 1443 | 131.9038 | 654.5928 | 0.161796 | 0.682656 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;concentration |
| h4_real_yield_proxy_momentum_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 306 | 251.2082 | 1194.5654 | 0.409761 | 1.863491 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;sample_size;concentration;activity |
| h4_treasury_curve_stress_momentum_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 975 | 100.0 | 300.5803 | 0.247986 | 1.119923 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;concentration;activity |
| h4_vix_risk_off_reversal_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 504 | 100.0 | 243.0016 | 0.29159 | 1.330496 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;concentration |
| h4_walk_forward_knn_momentum_state_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 5013 | 100.0 | 292.6321 | 0.117498 | 0.490744 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;concentration;activity |
| liquidity_sweep_continuation_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 12222 | 100.0 | 100.0 | 0.043763 | 0.195929 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;no_catastrophic_failure;concentration |
| liquidity_sweep_reversal_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 3906 | 100.0 | 100.0 | 0.075868 | 0.335886 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;no_catastrophic_failure;concentration |
| london_fix_continuation_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 4821 | 100.0 | 100.0 | 0.064478 | 0.319355 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;concentration |
| m15_inside_bar_breakout_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 7170 | 100.0 | 100.0 | 0.054633 | 0.243609 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;concentration |
| m15_two_bar_exhaustion_reversal_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 12282 | 100.0 | 100.0 | 0.053249 | 0.232785 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;no_catastrophic_failure;concentration |
| m15_two_bar_impulse_continuation_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 11191 | 100.0 | 100.0 | 0.048188 | 0.230759 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;no_catastrophic_failure;concentration |
| m5_impulse_continuation_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 20346 | 100.0 | 100.0 | 0.03133 | 0.148409 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;no_catastrophic_failure;concentration |
| ny_am_pullback_continuation_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 3195 | 100.0 | 100.0 | 0.074729 | 0.366887 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;concentration |
| ny_failed_london_reversal_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 3369 | 105.3398 | 520.4927 | 0.077302 | 0.37158 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;concentration |
| ny_london_overlap_compression_break_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 135 | 327.2039 | 327.2039 | 0.844001 | 1.020589 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;sample_size;concentration;activity;cost_sensitivity |
| opening_drive_failed_continuation_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 2208 | 100.0 | 100.0 | 0.091738 | 0.448952 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;concentration |
| post_spike_short_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 1860 | 495.1683 | 2221.5365 | 0.098392 | 0.468973 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;concentration |
| previous_day_extreme_retest_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 5295 | 100.0 | 333.617 | 0.072168 | 0.325522 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;no_catastrophic_failure;concentration |
| range_mr | REJECTED_OR_RESEARCH | FAIL | 9 | 24 | 100.0 | 100.0 | 0.0 | 0.0 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;sample_size;concentration;activity;cost_sensitivity |
| round_number_retest_v0 | REJECTED_OR_RESEARCH | PASS | 9 | 47388 | 0.7623 | 3.7948 | 0.019751 | 0.098656 | NOT_ABSOLUTE_CONCENTRATION_FAIL | none |
| session_extreme_retest_v0 | REJECTED_OR_RESEARCH | PASS | 9 | 23727 | 0.8203 | 4.056 | 0.025399 | 0.126433 | NOT_ABSOLUTE_CONCENTRATION_FAIL | none |
| session_vwap_reclaim_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 4806 | 100.0 | 100.0 | 0.061582 | 0.301236 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;no_catastrophic_failure;concentration |
| squeeze_breakout_long_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 1800 | 100.0 | 163.3252 | 0.095484 | 0.463688 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;concentration |
| symbol_round_sweep_reversal_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 9609 | 100.0 | 379.1626 | 0.057126 | 0.272656 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;no_catastrophic_failure;concentration |
| trend_pullback | REJECTED_OR_RESEARCH | FAIL | 9 | 27576 | 164.5178 | 228.471 | 0.348799 | 0.459661 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;no_catastrophic_failure;concentration |
| w1_d1_momentum_continuation_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 498 | 70.2727 | 337.7604 | 0.235291 | 1.026235 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;concentration |
| weekly_level_reclaim_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 1083 | 100.0 | 100.0 | 0.133429 | 0.60837 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;concentration |
| weekly_open_reversion_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 1878 | 149.5025 | 372.9627 | 0.960612 | 2.413121 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;no_catastrophic_failure;concentration |
| xag_lead_xau_followthrough_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 7608 | 100.0 | 121.4003 | 0.183137 | 0.43421 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;concentration |
| xau_xag_fx_composite_reversion_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 4704 | 100.0 | 159.6138 | 0.216725 | 0.67042 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;concentration |
| xau_xag_relative_value_v0 | REJECTED_OR_RESEARCH | FAIL | 9 | 936 | 272.0114 | 1349.4661 | 0.143336 | 0.709778 | REVIEW_NORMALIZED_CONTEXT | multi_cell_survival;concentration |
