# PHASE0 REALITY CHECK - FAMILY CLUSTERED

Overall status: PASS
Generated at UTC: 2026-05-29T12:56:03+00:00
Method: D2_FAMILY_CLUSTERED_V0
Approved expert representative: breakout_retest
Approved family under test: breakout_retest_family
Reviewer/owner accepted method: true

## Boundary

- This report does not modify `PHASE0_REALITY_CHECK.md`.
- This report does not convert the current candidate-level D2 FAIL into PASS.
- Phase 2 readiness effect: Method acceptance flag was supplied; readiness still depends on other gates.
- Same-family variants are not diversification.

## Method

This diagnostic applies the same fixed-notional monthly R-series White Reality Check and SPA-style bootstrap to pre-registered family representatives. The breakout-retest family uses `breakout_retest` as its fixed representative; same-family variants are listed in the assignment table and excluded from pairwise SPA as variants, not as hidden alternatives.

- Bootstrap iterations: 5000
- Circular block length: 3 month(s)
- Maximum accepted p-value: 0.1
- Effective accepted p-value: 0.01
- Family universes with at least 30 non-empty representatives are tightened to alpha = 0.01.
- Months in panel: 108
- Families in panel: 67

## White Reality Check

| Winner Family | White p | q90 R | q95 R | q99 R |
| --- | --- | --- | --- | --- |
| breakout_retest_family | 0.0002 | 0.8137 | 1.0026 | 1.3780 |

## Family Means

| Family | Mean Monthly R | Total R | Role |
| --- | --- | --- | --- |
| asia_range_london_breakout_v0 | -0.6926 | -74.80 | alternative_family |
| asia_range_london_failed_break_reversal_v0 | -0.3749 | -40.49 | alternative_family |
| breakout_retest_family | 12.9666 | 1400.40 | approved_family |
| cot_gold_positioning_reversal_v0 | -0.0025 | -0.27 | alternative_family |
| d1_compression_h4_expansion_v0 | 0.0063 | 0.68 | alternative_family |
| d1_inside_day_breakout_v0 | 0.0282 | 3.05 | alternative_family |
| d1_momentum_h4_pullback_v0 | 0.1090 | 11.77 | alternative_family |
| d1_multi_day_exhaustion_reversion_v0 | -0.0058 | -0.63 | alternative_family |
| d1_outside_day_followthrough_v0 | -0.0655 | -7.07 | alternative_family |
| d1_volatility_expansion_reversal_v0 | -0.0029 | -0.32 | alternative_family |
| d1_w1_momentum_h4_pullback_v0 | 0.0808 | 8.73 | alternative_family |
| daily_pivot_reclaim_v0 | -0.2632 | -28.43 | alternative_family |
| emr_inactivity_long_v0 | 0.0022 | 0.24 | alternative_family |
| extreme_activity_mean_reversion_v0 | -0.1063 | -11.48 | alternative_family |
| gold_fx_proxy_divergence_v0 | -0.0548 | -5.92 | alternative_family |
| h1_calendar_drift_state_v0 | -0.3297 | -35.61 | alternative_family |
| h1_gdx_gld_trend_confirmation_v0 | -0.0620 | -6.69 | alternative_family |
| h1_m5_path_skew_reversal_v0 | -0.1238 | -13.37 | alternative_family |
| h1_macro_composite_pullback_v0 | 0.0234 | 2.52 | alternative_family |
| h1_macro_event_aftershock_v0 | -0.0144 | -1.55 | alternative_family |
| h1_return_autocorrelation_state_v0 | -0.0130 | -1.40 | alternative_family |
| h1_smooth_trend_exhaustion_reversal_v0 | -0.0828 | -8.95 | alternative_family |
| h1_tick_volume_climax_reversal_v0 | -0.2831 | -30.57 | alternative_family |
| h1_volatility_squeeze_breakout_v0 | -0.0040 | -0.44 | alternative_family |
| h1_walk_forward_linear_state_v0 | 0.1149 | 12.41 | alternative_family |
| h4_breakeven_inflation_momentum_v0 | 0.1254 | 13.55 | alternative_family |
| h4_credit_spread_stress_momentum_v0 | -0.0582 | -6.28 | alternative_family |
| h4_d1_momentum_expansion_continuation_v0 | 0.0497 | 5.37 | alternative_family |
| h4_financial_conditions_stress_reversal_v0 | -0.0266 | -2.87 | alternative_family |
| h4_gdx_gld_miner_divergence_v0 | 0.0050 | 0.54 | alternative_family |
| h4_gld_etf_flow_reversal_v0 | 0.0583 | 6.30 | alternative_family |
| h4_gld_etf_flow_reversal_v1 | 0.0067 | 0.72 | alternative_family |
| h4_gold_futures_volume_climax_v0 | -0.0095 | -1.02 | alternative_family |
| h4_gvz_volatility_panic_reversal_v0 | -0.0115 | -1.24 | alternative_family |
| h4_inside_bar_d1_momentum_breakout_v0 | 0.0646 | 6.98 | alternative_family |
| h4_macro_composite_risk_state_v0 | 0.0742 | 8.01 | alternative_family |
| h4_macro_composite_risk_state_v1 | 0.0287 | 3.10 | alternative_family |
| h4_policy_uncertainty_safe_haven_v0 | 0.1535 | 16.58 | alternative_family |
| h4_real_yield_proxy_momentum_v0 | 0.0518 | 5.59 | alternative_family |
| h4_treasury_curve_stress_momentum_v0 | 0.0529 | 5.71 | alternative_family |
| h4_us_session_liquidity_reversal_v0 | 0.0107 | 1.16 | alternative_family |
| h4_vix_risk_off_reversal_v0 | 0.0247 | 2.67 | alternative_family |
| h4_walk_forward_knn_momentum_state_v0 | 0.0689 | 7.44 | alternative_family |
| liquidity_sweep_continuation_v0 | -0.9719 | -104.97 | alternative_family |
| liquidity_sweep_reversal_v0 | -0.5052 | -54.56 | alternative_family |
| london_fix_continuation_v0 | -0.1354 | -14.63 | alternative_family |
| m15_inside_bar_breakout_v0 | -0.0846 | -9.14 | alternative_family |
| m15_two_bar_exhaustion_reversal_v0 | -1.7034 | -183.97 | alternative_family |
| m15_two_bar_impulse_continuation_v0 | -0.3915 | -42.28 | alternative_family |
| m5_impulse_continuation_v0 | -1.0317 | -111.42 | alternative_family |
| ny_am_pullback_continuation_v0 | -0.1281 | -13.84 | alternative_family |
| ny_failed_london_reversal_v0 | -0.0398 | -4.30 | alternative_family |
| ny_london_overlap_compression_break_v0 | -0.0100 | -1.08 | alternative_family |
| opening_drive_failed_continuation_v0 | -0.1762 | -19.03 | alternative_family |
| post_spike_short_v0 | -0.0660 | -7.12 | alternative_family |
| previous_day_extreme_retest_v0 | -0.1903 | -20.55 | alternative_family |
| range_mr | -0.0375 | -4.05 | alternative_family |
| session_vwap_reclaim_v0 | -0.3606 | -38.95 | alternative_family |
| squeeze_breakout_long_v0 | 0.0374 | 4.03 | alternative_family |
| symbol_round_sweep_reversal_v0 | -0.6750 | -72.90 | alternative_family |
| trend_pullback | -1.8156 | -196.08 | alternative_family |
| w1_d1_momentum_continuation_v0 | 0.0523 | 5.64 | alternative_family |
| weekly_level_reclaim_v0 | -0.0925 | -9.99 | alternative_family |
| weekly_open_reversion_v0 | -0.1696 | -18.31 | alternative_family |
| xag_lead_xau_followthrough_v0 | -0.2563 | -27.68 | alternative_family |
| xau_xag_fx_composite_reversion_v0 | -0.1592 | -17.20 | alternative_family |
| xau_xag_relative_value_v0 | 0.0099 | 1.07 | alternative_family |

## SPA-Style Pairwise Checks

| Alternative Family | Status | Mean Edge R | SPA p | Bootstrap q95 R |
| --- | --- | --- | --- | --- |
| asia_range_london_breakout_v0 | PASS | 13.6592 | 0.0002 | 0.9903 |
| asia_range_london_failed_break_reversal_v0 | PASS | 13.3415 | 0.0002 | 1.0454 |
| cot_gold_positioning_reversal_v0 | PASS | 12.9691 | 0.0002 | 0.9824 |
| d1_compression_h4_expansion_v0 | PASS | 12.9603 | 0.0002 | 1.0037 |
| d1_inside_day_breakout_v0 | PASS | 12.9384 | 0.0002 | 1.0239 |
| d1_momentum_h4_pullback_v0 | PASS | 12.8577 | 0.0002 | 1.0280 |
| d1_multi_day_exhaustion_reversion_v0 | PASS | 12.9724 | 0.0002 | 0.9797 |
| d1_outside_day_followthrough_v0 | PASS | 13.0321 | 0.0002 | 1.0177 |
| d1_volatility_expansion_reversal_v0 | PASS | 12.9696 | 0.0002 | 0.9586 |
| d1_w1_momentum_h4_pullback_v0 | PASS | 12.8858 | 0.0002 | 1.0154 |
| daily_pivot_reclaim_v0 | PASS | 13.2298 | 0.0002 | 1.0506 |
| emr_inactivity_long_v0 | PASS | 12.9644 | 0.0002 | 1.0365 |
| extreme_activity_mean_reversion_v0 | PASS | 13.0730 | 0.0002 | 1.0114 |
| gold_fx_proxy_divergence_v0 | PASS | 13.0214 | 0.0002 | 0.9790 |
| h1_calendar_drift_state_v0 | PASS | 13.2963 | 0.0002 | 1.1410 |
| h1_gdx_gld_trend_confirmation_v0 | PASS | 13.0286 | 0.0002 | 0.9956 |
| h1_m5_path_skew_reversal_v0 | PASS | 13.0905 | 0.0002 | 1.0239 |
| h1_macro_composite_pullback_v0 | PASS | 12.9433 | 0.0002 | 1.0080 |
| h1_macro_event_aftershock_v0 | PASS | 12.9810 | 0.0002 | 0.9807 |
| h1_return_autocorrelation_state_v0 | PASS | 12.9796 | 0.0002 | 1.0548 |
| h1_smooth_trend_exhaustion_reversal_v0 | PASS | 13.0495 | 0.0002 | 1.0320 |
| h1_tick_volume_climax_reversal_v0 | PASS | 13.2497 | 0.0002 | 1.0038 |
| h1_volatility_squeeze_breakout_v0 | PASS | 12.9707 | 0.0002 | 1.0085 |
| h1_walk_forward_linear_state_v0 | PASS | 12.8517 | 0.0002 | 1.1053 |
| h4_breakeven_inflation_momentum_v0 | PASS | 12.8412 | 0.0002 | 0.9967 |
| h4_credit_spread_stress_momentum_v0 | PASS | 13.0248 | 0.0002 | 1.0083 |
| h4_d1_momentum_expansion_continuation_v0 | PASS | 12.9169 | 0.0002 | 0.9859 |
| h4_financial_conditions_stress_reversal_v0 | PASS | 12.9932 | 0.0002 | 0.9885 |
| h4_gdx_gld_miner_divergence_v0 | PASS | 12.9616 | 0.0002 | 1.0070 |
| h4_gld_etf_flow_reversal_v0 | PASS | 12.9083 | 0.0002 | 0.9924 |
| h4_gld_etf_flow_reversal_v1 | PASS | 12.9600 | 0.0002 | 1.0175 |
| h4_gold_futures_volume_climax_v0 | PASS | 12.9761 | 0.0002 | 1.0099 |
| h4_gvz_volatility_panic_reversal_v0 | PASS | 12.9781 | 0.0002 | 1.0055 |
| h4_inside_bar_d1_momentum_breakout_v0 | PASS | 12.9020 | 0.0002 | 0.9953 |
| h4_macro_composite_risk_state_v0 | PASS | 12.8924 | 0.0002 | 0.9843 |
| h4_macro_composite_risk_state_v1 | PASS | 12.9379 | 0.0002 | 0.9801 |
| h4_policy_uncertainty_safe_haven_v0 | PASS | 12.8131 | 0.0002 | 1.0219 |
| h4_real_yield_proxy_momentum_v0 | PASS | 12.9149 | 0.0002 | 0.9734 |
| h4_treasury_curve_stress_momentum_v0 | PASS | 12.9137 | 0.0002 | 0.9852 |
| h4_us_session_liquidity_reversal_v0 | PASS | 12.9559 | 0.0002 | 0.9978 |
| h4_vix_risk_off_reversal_v0 | PASS | 12.9419 | 0.0002 | 0.9849 |
| h4_walk_forward_knn_momentum_state_v0 | PASS | 12.8978 | 0.0002 | 1.0518 |
| liquidity_sweep_continuation_v0 | PASS | 13.9385 | 0.0002 | 1.0250 |
| liquidity_sweep_reversal_v0 | PASS | 13.4718 | 0.0002 | 1.0009 |
| london_fix_continuation_v0 | PASS | 13.1021 | 0.0002 | 1.0356 |
| m15_inside_bar_breakout_v0 | PASS | 13.0512 | 0.0002 | 1.0305 |
| m15_two_bar_exhaustion_reversal_v0 | PASS | 14.6700 | 0.0002 | 1.1376 |
| m15_two_bar_impulse_continuation_v0 | PASS | 13.3581 | 0.0002 | 0.9865 |
| m5_impulse_continuation_v0 | PASS | 13.9983 | 0.0002 | 1.0093 |
| ny_am_pullback_continuation_v0 | PASS | 13.0947 | 0.0002 | 1.0026 |
| ny_failed_london_reversal_v0 | PASS | 13.0064 | 0.0002 | 1.0204 |
| ny_london_overlap_compression_break_v0 | PASS | 12.9767 | 0.0002 | 1.0282 |
| opening_drive_failed_continuation_v0 | PASS | 13.1428 | 0.0002 | 0.9892 |
| post_spike_short_v0 | PASS | 13.0326 | 0.0002 | 1.0181 |
| previous_day_extreme_retest_v0 | PASS | 13.1569 | 0.0002 | 0.9645 |
| range_mr | PASS | 13.0041 | 0.0002 | 1.0159 |
| session_vwap_reclaim_v0 | PASS | 13.3272 | 0.0002 | 0.9833 |
| squeeze_breakout_long_v0 | PASS | 12.9293 | 0.0002 | 1.0179 |
| symbol_round_sweep_reversal_v0 | PASS | 13.6416 | 0.0002 | 1.0485 |
| trend_pullback | PASS | 14.7822 | 0.0002 | 1.1382 |
| w1_d1_momentum_continuation_v0 | PASS | 12.9144 | 0.0002 | 0.9895 |
| weekly_level_reclaim_v0 | PASS | 13.0592 | 0.0002 | 1.0449 |
| weekly_open_reversion_v0 | PASS | 13.1362 | 0.0002 | 0.9409 |
| xag_lead_xau_followthrough_v0 | PASS | 13.2230 | 0.0002 | 1.0290 |
| xau_xag_fx_composite_reversion_v0 | PASS | 13.1259 | 0.0002 | 1.0158 |
| xau_xag_relative_value_v0 | PASS | 12.9567 | 0.0002 | 1.0288 |

## Excluded Same-Family Variants

| Expert | Family | Representative | Reason |
| --- | --- | --- | --- |
| quarter_round_retest_v0 | breakout_retest_family | breakout_retest | Explicitly documented same-family level/retest variant; not diversification. |
| round_number_retest_v0 | breakout_retest_family | breakout_retest | Explicitly documented same-family level/retest variant; not diversification. |
| session_extreme_retest_v0 | breakout_retest_family | breakout_retest | Explicitly documented same-family level/retest variant; not diversification. |
| swing_breakout_retest_v0 | breakout_retest_family | breakout_retest | Explicitly documented same-family level/retest variant; not diversification. |
| symbol_normalized_round_retest_v0 | breakout_retest_family | breakout_retest | Explicitly documented same-family level/retest variant; not diversification. |

## Assignment Preview

| Expert | Family | Representative | Role | Included |
| --- | --- | --- | --- | --- |
| asia_range_london_breakout_v0 | asia_range_london_breakout_v0 | asia_range_london_breakout_v0 | independent_representative | true |
| asia_range_london_failed_break_reversal_v0 | asia_range_london_failed_break_reversal_v0 | asia_range_london_failed_break_reversal_v0 | independent_representative | true |
| breakout_retest | breakout_retest_family | breakout_retest | family_representative | true |
| cot_gold_positioning_reversal_v0 | cot_gold_positioning_reversal_v0 | cot_gold_positioning_reversal_v0 | independent_representative | true |
| d1_compression_h4_expansion_v0 | d1_compression_h4_expansion_v0 | d1_compression_h4_expansion_v0 | independent_representative | true |
| d1_inside_day_breakout_v0 | d1_inside_day_breakout_v0 | d1_inside_day_breakout_v0 | independent_representative | true |
| d1_momentum_h4_pullback_v0 | d1_momentum_h4_pullback_v0 | d1_momentum_h4_pullback_v0 | independent_representative | true |
| d1_multi_day_exhaustion_reversion_v0 | d1_multi_day_exhaustion_reversion_v0 | d1_multi_day_exhaustion_reversion_v0 | independent_representative | true |
| d1_outside_day_followthrough_v0 | d1_outside_day_followthrough_v0 | d1_outside_day_followthrough_v0 | independent_representative | true |
| d1_volatility_expansion_reversal_v0 | d1_volatility_expansion_reversal_v0 | d1_volatility_expansion_reversal_v0 | independent_representative | true |
| d1_w1_momentum_h4_pullback_v0 | d1_w1_momentum_h4_pullback_v0 | d1_w1_momentum_h4_pullback_v0 | independent_representative | true |
| daily_pivot_reclaim_v0 | daily_pivot_reclaim_v0 | daily_pivot_reclaim_v0 | independent_representative | true |
| emr_inactivity_long_v0 | emr_inactivity_long_v0 | emr_inactivity_long_v0 | independent_representative | true |
| extreme_activity_mean_reversion_v0 | extreme_activity_mean_reversion_v0 | extreme_activity_mean_reversion_v0 | independent_representative | true |
| gold_fx_proxy_divergence_v0 | gold_fx_proxy_divergence_v0 | gold_fx_proxy_divergence_v0 | independent_representative | true |
| h1_calendar_drift_state_v0 | h1_calendar_drift_state_v0 | h1_calendar_drift_state_v0 | independent_representative | true |
| h1_gdx_gld_trend_confirmation_v0 | h1_gdx_gld_trend_confirmation_v0 | h1_gdx_gld_trend_confirmation_v0 | independent_representative | true |
| h1_m5_path_skew_reversal_v0 | h1_m5_path_skew_reversal_v0 | h1_m5_path_skew_reversal_v0 | independent_representative | true |
| h1_macro_composite_pullback_v0 | h1_macro_composite_pullback_v0 | h1_macro_composite_pullback_v0 | independent_representative | true |
| h1_macro_event_aftershock_v0 | h1_macro_event_aftershock_v0 | h1_macro_event_aftershock_v0 | independent_representative | true |
| h1_return_autocorrelation_state_v0 | h1_return_autocorrelation_state_v0 | h1_return_autocorrelation_state_v0 | independent_representative | true |
| h1_smooth_trend_exhaustion_reversal_v0 | h1_smooth_trend_exhaustion_reversal_v0 | h1_smooth_trend_exhaustion_reversal_v0 | independent_representative | true |
| h1_tick_volume_climax_reversal_v0 | h1_tick_volume_climax_reversal_v0 | h1_tick_volume_climax_reversal_v0 | independent_representative | true |
| h1_volatility_squeeze_breakout_v0 | h1_volatility_squeeze_breakout_v0 | h1_volatility_squeeze_breakout_v0 | independent_representative | true |
| h1_walk_forward_linear_state_v0 | h1_walk_forward_linear_state_v0 | h1_walk_forward_linear_state_v0 | independent_representative | true |
| h4_breakeven_inflation_momentum_v0 | h4_breakeven_inflation_momentum_v0 | h4_breakeven_inflation_momentum_v0 | independent_representative | true |
| h4_credit_spread_stress_momentum_v0 | h4_credit_spread_stress_momentum_v0 | h4_credit_spread_stress_momentum_v0 | independent_representative | true |
| h4_d1_momentum_expansion_continuation_v0 | h4_d1_momentum_expansion_continuation_v0 | h4_d1_momentum_expansion_continuation_v0 | independent_representative | true |
| h4_financial_conditions_stress_reversal_v0 | h4_financial_conditions_stress_reversal_v0 | h4_financial_conditions_stress_reversal_v0 | independent_representative | true |
| h4_gdx_gld_miner_divergence_v0 | h4_gdx_gld_miner_divergence_v0 | h4_gdx_gld_miner_divergence_v0 | independent_representative | true |
| h4_gld_etf_flow_reversal_v0 | h4_gld_etf_flow_reversal_v0 | h4_gld_etf_flow_reversal_v0 | independent_representative | true |
| h4_gld_etf_flow_reversal_v1 | h4_gld_etf_flow_reversal_v1 | h4_gld_etf_flow_reversal_v1 | independent_representative | true |
| h4_gold_futures_volume_climax_v0 | h4_gold_futures_volume_climax_v0 | h4_gold_futures_volume_climax_v0 | independent_representative | true |
| h4_gvz_volatility_panic_reversal_v0 | h4_gvz_volatility_panic_reversal_v0 | h4_gvz_volatility_panic_reversal_v0 | independent_representative | true |
| h4_inside_bar_d1_momentum_breakout_v0 | h4_inside_bar_d1_momentum_breakout_v0 | h4_inside_bar_d1_momentum_breakout_v0 | independent_representative | true |
| h4_macro_composite_risk_state_v0 | h4_macro_composite_risk_state_v0 | h4_macro_composite_risk_state_v0 | independent_representative | true |
| h4_macro_composite_risk_state_v1 | h4_macro_composite_risk_state_v1 | h4_macro_composite_risk_state_v1 | independent_representative | true |
| h4_policy_uncertainty_safe_haven_v0 | h4_policy_uncertainty_safe_haven_v0 | h4_policy_uncertainty_safe_haven_v0 | independent_representative | true |
| h4_real_yield_proxy_momentum_v0 | h4_real_yield_proxy_momentum_v0 | h4_real_yield_proxy_momentum_v0 | independent_representative | true |
| h4_treasury_curve_stress_momentum_v0 | h4_treasury_curve_stress_momentum_v0 | h4_treasury_curve_stress_momentum_v0 | independent_representative | true |
| h4_us_session_liquidity_reversal_v0 | h4_us_session_liquidity_reversal_v0 | h4_us_session_liquidity_reversal_v0 | independent_representative | true |
| h4_vix_risk_off_reversal_v0 | h4_vix_risk_off_reversal_v0 | h4_vix_risk_off_reversal_v0 | independent_representative | true |
| h4_walk_forward_knn_momentum_state_v0 | h4_walk_forward_knn_momentum_state_v0 | h4_walk_forward_knn_momentum_state_v0 | independent_representative | true |
| liquidity_sweep_continuation_v0 | liquidity_sweep_continuation_v0 | liquidity_sweep_continuation_v0 | independent_representative | true |
| liquidity_sweep_reversal_v0 | liquidity_sweep_reversal_v0 | liquidity_sweep_reversal_v0 | independent_representative | true |
| london_fix_continuation_v0 | london_fix_continuation_v0 | london_fix_continuation_v0 | independent_representative | true |
| m15_inside_bar_breakout_v0 | m15_inside_bar_breakout_v0 | m15_inside_bar_breakout_v0 | independent_representative | true |
| m15_two_bar_exhaustion_reversal_v0 | m15_two_bar_exhaustion_reversal_v0 | m15_two_bar_exhaustion_reversal_v0 | independent_representative | true |
| m15_two_bar_impulse_continuation_v0 | m15_two_bar_impulse_continuation_v0 | m15_two_bar_impulse_continuation_v0 | independent_representative | true |
| m5_impulse_continuation_v0 | m5_impulse_continuation_v0 | m5_impulse_continuation_v0 | independent_representative | true |
| ny_am_pullback_continuation_v0 | ny_am_pullback_continuation_v0 | ny_am_pullback_continuation_v0 | independent_representative | true |
| ny_failed_london_reversal_v0 | ny_failed_london_reversal_v0 | ny_failed_london_reversal_v0 | independent_representative | true |
| ny_london_overlap_compression_break_v0 | ny_london_overlap_compression_break_v0 | ny_london_overlap_compression_break_v0 | independent_representative | true |
| opening_drive_failed_continuation_v0 | opening_drive_failed_continuation_v0 | opening_drive_failed_continuation_v0 | independent_representative | true |
| post_spike_short_v0 | post_spike_short_v0 | post_spike_short_v0 | independent_representative | true |
| previous_day_extreme_retest_v0 | previous_day_extreme_retest_v0 | previous_day_extreme_retest_v0 | independent_representative | true |
| quarter_round_retest_v0 | breakout_retest_family | breakout_retest | same_family_excluded_from_pairwise_spa | false |
| range_mr | range_mr | range_mr | independent_representative | true |
| round_number_retest_v0 | breakout_retest_family | breakout_retest | same_family_excluded_from_pairwise_spa | false |
| session_extreme_retest_v0 | breakout_retest_family | breakout_retest | same_family_excluded_from_pairwise_spa | false |
| session_vwap_reclaim_v0 | session_vwap_reclaim_v0 | session_vwap_reclaim_v0 | independent_representative | true |
| squeeze_breakout_long_v0 | squeeze_breakout_long_v0 | squeeze_breakout_long_v0 | independent_representative | true |
| swing_breakout_retest_v0 | breakout_retest_family | breakout_retest | same_family_excluded_from_pairwise_spa | false |
| symbol_normalized_round_retest_v0 | breakout_retest_family | breakout_retest | same_family_excluded_from_pairwise_spa | false |
| symbol_round_sweep_reversal_v0 | symbol_round_sweep_reversal_v0 | symbol_round_sweep_reversal_v0 | independent_representative | true |
| trend_pullback | trend_pullback | trend_pullback | independent_representative | true |
| w1_d1_momentum_continuation_v0 | w1_d1_momentum_continuation_v0 | w1_d1_momentum_continuation_v0 | independent_representative | true |
| weekly_level_reclaim_v0 | weekly_level_reclaim_v0 | weekly_level_reclaim_v0 | independent_representative | true |
| weekly_open_reversion_v0 | weekly_open_reversion_v0 | weekly_open_reversion_v0 | independent_representative | true |
| xag_lead_xau_followthrough_v0 | xag_lead_xau_followthrough_v0 | xag_lead_xau_followthrough_v0 | independent_representative | true |
| xau_xag_fx_composite_reversion_v0 | xau_xag_fx_composite_reversion_v0 | xau_xag_fx_composite_reversion_v0 | independent_representative | true |
| xau_xag_relative_value_v0 | xau_xag_relative_value_v0 | xau_xag_relative_value_v0 | independent_representative | true |

## Interpretation

A statistical PASS here means the pre-registered breakout-retest family representative survived the family-level multiple-testing diagnostic against independent representatives. It does not choose between same-family deployment variants, does not provide diversification, and does not authorize Phase 2 paper-mode execution without reviewer/owner method acceptance plus all separate soak, measured-cost, VPS, and approval gates.

Assignments are written to `outputs/reports/PHASE0_REALITY_CHECK_FAMILY_ASSIGNMENTS.csv`.
