# PHASE0 REALITY CHECK

Status: FAIL
Generated at UTC: 2026-05-29T12:54:36+00:00
Approved expert under test: breakout_retest

## Method

This report applies a White Reality Check and SPA-style pairwise bootstrap to monthly fixed-notional R returns for the Phase 0 expert family. Each expert's monthly value is the average monthly R sum across its matrix trade ledgers, which keeps cost/broker cells from turning into separate optimized candidates and avoids compounding-dollar scale artifacts.

- Bootstrap iterations: 5000
- Circular block length: 3 month(s)
- Maximum accepted p-value: 0.1
- Effective accepted p-value: 0.01
- Candidate universes with at least 30 non-empty matrix-ledger candidates are tightened to alpha = 0.01.
- Months in panel: 108

## White Reality Check

| Winner | White p | q90 R | q95 R | q99 R |
| --- | --- | --- | --- | --- |
| quarter_round_retest_v0 | 0.0002 | 1.3556 | 1.6608 | 2.3193 |

## Expert Means

| Expert | Mean Monthly R | Total R | Role |
| --- | --- | --- | --- |
| asia_range_london_breakout_v0 | -0.6926 | -74.80 | alternative |
| asia_range_london_failed_break_reversal_v0 | -0.3749 | -40.49 | alternative |
| breakout_retest | 12.9666 | 1400.40 | approved |
| cot_gold_positioning_reversal_v0 | -0.0025 | -0.27 | alternative |
| d1_compression_h4_expansion_v0 | 0.0063 | 0.68 | alternative |
| d1_inside_day_breakout_v0 | 0.0282 | 3.05 | alternative |
| d1_momentum_h4_pullback_v0 | 0.1090 | 11.77 | alternative |
| d1_multi_day_exhaustion_reversion_v0 | -0.0058 | -0.63 | alternative |
| d1_outside_day_followthrough_v0 | -0.0655 | -7.07 | alternative |
| d1_volatility_expansion_reversal_v0 | -0.0029 | -0.32 | alternative |
| d1_w1_momentum_h4_pullback_v0 | 0.0808 | 8.73 | alternative |
| daily_pivot_reclaim_v0 | -0.2632 | -28.43 | alternative |
| emr_inactivity_long_v0 | 0.0022 | 0.24 | alternative |
| extreme_activity_mean_reversion_v0 | -0.1063 | -11.48 | alternative |
| gold_fx_proxy_divergence_v0 | -0.0548 | -5.92 | alternative |
| h1_calendar_drift_state_v0 | -0.3297 | -35.61 | alternative |
| h1_gdx_gld_trend_confirmation_v0 | -0.0620 | -6.69 | alternative |
| h1_m5_path_skew_reversal_v0 | -0.1238 | -13.37 | alternative |
| h1_macro_composite_pullback_v0 | 0.0234 | 2.52 | alternative |
| h1_macro_event_aftershock_v0 | -0.0144 | -1.55 | alternative |
| h1_return_autocorrelation_state_v0 | -0.0130 | -1.40 | alternative |
| h1_smooth_trend_exhaustion_reversal_v0 | -0.0828 | -8.95 | alternative |
| h1_tick_volume_climax_reversal_v0 | -0.2831 | -30.57 | alternative |
| h1_volatility_squeeze_breakout_v0 | -0.0040 | -0.44 | alternative |
| h1_walk_forward_linear_state_v0 | 0.1149 | 12.41 | alternative |
| h4_breakeven_inflation_momentum_v0 | 0.1254 | 13.55 | alternative |
| h4_credit_spread_stress_momentum_v0 | -0.0582 | -6.28 | alternative |
| h4_d1_momentum_expansion_continuation_v0 | 0.0497 | 5.37 | alternative |
| h4_financial_conditions_stress_reversal_v0 | -0.0266 | -2.87 | alternative |
| h4_gdx_gld_miner_divergence_v0 | 0.0050 | 0.54 | alternative |
| h4_gld_etf_flow_reversal_v0 | 0.0583 | 6.30 | alternative |
| h4_gld_etf_flow_reversal_v1 | 0.0067 | 0.72 | alternative |
| h4_gold_futures_volume_climax_v0 | -0.0095 | -1.02 | alternative |
| h4_gvz_volatility_panic_reversal_v0 | -0.0115 | -1.24 | alternative |
| h4_inside_bar_d1_momentum_breakout_v0 | 0.0646 | 6.98 | alternative |
| h4_macro_composite_risk_state_v0 | 0.0742 | 8.01 | alternative |
| h4_macro_composite_risk_state_v1 | 0.0287 | 3.10 | alternative |
| h4_policy_uncertainty_safe_haven_v0 | 0.1535 | 16.58 | alternative |
| h4_real_yield_proxy_momentum_v0 | 0.0518 | 5.59 | alternative |
| h4_treasury_curve_stress_momentum_v0 | 0.0529 | 5.71 | alternative |
| h4_us_session_liquidity_reversal_v0 | 0.0107 | 1.16 | alternative |
| h4_vix_risk_off_reversal_v0 | 0.0247 | 2.67 | alternative |
| h4_walk_forward_knn_momentum_state_v0 | 0.0689 | 7.44 | alternative |
| liquidity_sweep_continuation_v0 | -0.9719 | -104.97 | alternative |
| liquidity_sweep_reversal_v0 | -0.5052 | -54.56 | alternative |
| london_fix_continuation_v0 | -0.1354 | -14.63 | alternative |
| m15_inside_bar_breakout_v0 | -0.0846 | -9.14 | alternative |
| m15_two_bar_exhaustion_reversal_v0 | -1.7034 | -183.97 | alternative |
| m15_two_bar_impulse_continuation_v0 | -0.3915 | -42.28 | alternative |
| m5_impulse_continuation_v0 | -1.0317 | -111.42 | alternative |
| ny_am_pullback_continuation_v0 | -0.1281 | -13.84 | alternative |
| ny_failed_london_reversal_v0 | -0.0398 | -4.30 | alternative |
| ny_london_overlap_compression_break_v0 | -0.0100 | -1.08 | alternative |
| opening_drive_failed_continuation_v0 | -0.1762 | -19.03 | alternative |
| post_spike_short_v0 | -0.0660 | -7.12 | alternative |
| previous_day_extreme_retest_v0 | -0.1903 | -20.55 | alternative |
| quarter_round_retest_v0 | 16.7597 | 1810.05 | alternative |
| range_mr | -0.0375 | -4.05 | alternative |
| round_number_retest_v0 | 11.0507 | 1193.48 | alternative |
| session_extreme_retest_v0 | 5.4747 | 591.27 | alternative |
| session_vwap_reclaim_v0 | -0.3606 | -38.95 | alternative |
| squeeze_breakout_long_v0 | 0.0374 | 4.03 | alternative |
| swing_breakout_retest_v0 | 11.2019 | 1209.81 | alternative |
| symbol_normalized_round_retest_v0 | 11.0507 | 1193.48 | alternative |
| symbol_round_sweep_reversal_v0 | -0.6750 | -72.90 | alternative |
| trend_pullback | -1.8156 | -196.08 | alternative |
| w1_d1_momentum_continuation_v0 | 0.0523 | 5.64 | alternative |
| weekly_level_reclaim_v0 | -0.0925 | -9.99 | alternative |
| weekly_open_reversion_v0 | -0.1696 | -18.31 | alternative |
| xag_lead_xau_followthrough_v0 | -0.2563 | -27.68 | alternative |
| xau_xag_fx_composite_reversion_v0 | -0.1592 | -17.20 | alternative |
| xau_xag_relative_value_v0 | 0.0099 | 1.07 | alternative |

## SPA-Style Pairwise Checks

| Alternative | Status | Mean Edge R | SPA p | Bootstrap q95 R |
| --- | --- | --- | --- | --- |
| asia_range_london_breakout_v0 | PASS | 13.6592 | 0.0002 | 1.0179 |
| asia_range_london_failed_break_reversal_v0 | PASS | 13.3415 | 0.0002 | 1.0531 |
| cot_gold_positioning_reversal_v0 | PASS | 12.9691 | 0.0002 | 1.0392 |
| d1_compression_h4_expansion_v0 | PASS | 12.9603 | 0.0002 | 1.0128 |
| d1_inside_day_breakout_v0 | PASS | 12.9384 | 0.0002 | 1.0038 |
| d1_momentum_h4_pullback_v0 | PASS | 12.8577 | 0.0002 | 0.9911 |
| d1_multi_day_exhaustion_reversion_v0 | PASS | 12.9724 | 0.0002 | 0.9785 |
| d1_outside_day_followthrough_v0 | PASS | 13.0321 | 0.0002 | 1.0175 |
| d1_volatility_expansion_reversal_v0 | PASS | 12.9696 | 0.0002 | 0.9779 |
| d1_w1_momentum_h4_pullback_v0 | PASS | 12.8858 | 0.0002 | 0.9856 |
| daily_pivot_reclaim_v0 | PASS | 13.2298 | 0.0002 | 1.0225 |
| emr_inactivity_long_v0 | PASS | 12.9644 | 0.0002 | 0.9902 |
| extreme_activity_mean_reversion_v0 | PASS | 13.0730 | 0.0002 | 0.9796 |
| gold_fx_proxy_divergence_v0 | PASS | 13.0214 | 0.0002 | 1.0045 |
| h1_calendar_drift_state_v0 | PASS | 13.2963 | 0.0002 | 1.1851 |
| h1_gdx_gld_trend_confirmation_v0 | PASS | 13.0286 | 0.0002 | 1.0235 |
| h1_m5_path_skew_reversal_v0 | PASS | 13.0905 | 0.0002 | 1.0717 |
| h1_macro_composite_pullback_v0 | PASS | 12.9433 | 0.0002 | 1.0151 |
| h1_macro_event_aftershock_v0 | PASS | 12.9810 | 0.0002 | 1.0030 |
| h1_return_autocorrelation_state_v0 | PASS | 12.9796 | 0.0002 | 1.0492 |
| h1_smooth_trend_exhaustion_reversal_v0 | PASS | 13.0495 | 0.0002 | 1.0341 |
| h1_tick_volume_climax_reversal_v0 | PASS | 13.2497 | 0.0002 | 1.0088 |
| h1_volatility_squeeze_breakout_v0 | PASS | 12.9707 | 0.0002 | 0.9941 |
| h1_walk_forward_linear_state_v0 | PASS | 12.8517 | 0.0002 | 1.1219 |
| h4_breakeven_inflation_momentum_v0 | PASS | 12.8412 | 0.0002 | 1.0243 |
| h4_credit_spread_stress_momentum_v0 | PASS | 13.0248 | 0.0002 | 1.0063 |
| h4_d1_momentum_expansion_continuation_v0 | PASS | 12.9169 | 0.0002 | 1.0014 |
| h4_financial_conditions_stress_reversal_v0 | PASS | 12.9932 | 0.0002 | 0.9754 |
| h4_gdx_gld_miner_divergence_v0 | PASS | 12.9616 | 0.0002 | 1.0276 |
| h4_gld_etf_flow_reversal_v0 | PASS | 12.9083 | 0.0002 | 0.9942 |
| h4_gld_etf_flow_reversal_v1 | PASS | 12.9600 | 0.0002 | 1.0090 |
| h4_gold_futures_volume_climax_v0 | PASS | 12.9761 | 0.0002 | 0.9912 |
| h4_gvz_volatility_panic_reversal_v0 | PASS | 12.9781 | 0.0002 | 1.0159 |
| h4_inside_bar_d1_momentum_breakout_v0 | PASS | 12.9020 | 0.0002 | 1.0105 |
| h4_macro_composite_risk_state_v0 | PASS | 12.8924 | 0.0002 | 0.9815 |
| h4_macro_composite_risk_state_v1 | PASS | 12.9379 | 0.0002 | 0.9742 |
| h4_policy_uncertainty_safe_haven_v0 | PASS | 12.8131 | 0.0002 | 1.0150 |
| h4_real_yield_proxy_momentum_v0 | PASS | 12.9149 | 0.0002 | 1.0223 |
| h4_treasury_curve_stress_momentum_v0 | PASS | 12.9137 | 0.0002 | 1.0089 |
| h4_us_session_liquidity_reversal_v0 | PASS | 12.9559 | 0.0002 | 1.0160 |
| h4_vix_risk_off_reversal_v0 | PASS | 12.9419 | 0.0002 | 0.9942 |
| h4_walk_forward_knn_momentum_state_v0 | PASS | 12.8978 | 0.0002 | 1.0616 |
| liquidity_sweep_continuation_v0 | PASS | 13.9385 | 0.0002 | 1.0675 |
| liquidity_sweep_reversal_v0 | PASS | 13.4718 | 0.0002 | 1.0156 |
| london_fix_continuation_v0 | PASS | 13.1021 | 0.0002 | 1.0128 |
| m15_inside_bar_breakout_v0 | PASS | 13.0512 | 0.0002 | 1.0443 |
| m15_two_bar_exhaustion_reversal_v0 | PASS | 14.6700 | 0.0002 | 1.1920 |
| m15_two_bar_impulse_continuation_v0 | PASS | 13.3581 | 0.0002 | 1.0300 |
| m5_impulse_continuation_v0 | PASS | 13.9983 | 0.0002 | 1.0362 |
| ny_am_pullback_continuation_v0 | PASS | 13.0947 | 0.0002 | 0.9596 |
| ny_failed_london_reversal_v0 | PASS | 13.0064 | 0.0002 | 1.0332 |
| ny_london_overlap_compression_break_v0 | PASS | 12.9767 | 0.0002 | 1.0133 |
| opening_drive_failed_continuation_v0 | PASS | 13.1428 | 0.0002 | 1.0460 |
| post_spike_short_v0 | PASS | 13.0326 | 0.0002 | 1.0309 |
| previous_day_extreme_retest_v0 | PASS | 13.1569 | 0.0002 | 0.9848 |
| quarter_round_retest_v0 | FAIL | -3.7931 | 0.9998 | 1.7132 |
| range_mr | PASS | 13.0041 | 0.0002 | 0.9772 |
| round_number_retest_v0 | FAIL | 1.9159 | 0.0172 | 1.5071 |
| session_extreme_retest_v0 | PASS | 7.4919 | 0.0002 | 1.0458 |
| session_vwap_reclaim_v0 | PASS | 13.3272 | 0.0002 | 0.9548 |
| squeeze_breakout_long_v0 | PASS | 12.9293 | 0.0002 | 1.0479 |
| swing_breakout_retest_v0 | PASS | 1.7647 | 0.0002 | 0.3983 |
| symbol_normalized_round_retest_v0 | FAIL | 1.9159 | 0.0142 | 1.4761 |
| symbol_round_sweep_reversal_v0 | PASS | 13.6416 | 0.0002 | 1.0272 |
| trend_pullback | PASS | 14.7822 | 0.0002 | 1.1470 |
| w1_d1_momentum_continuation_v0 | PASS | 12.9144 | 0.0002 | 0.9750 |
| weekly_level_reclaim_v0 | PASS | 13.0592 | 0.0002 | 1.0354 |
| weekly_open_reversion_v0 | PASS | 13.1362 | 0.0002 | 0.9434 |
| xag_lead_xau_followthrough_v0 | PASS | 13.2230 | 0.0002 | 1.0305 |
| xau_xag_fx_composite_reversion_v0 | PASS | 13.1259 | 0.0002 | 1.0541 |
| xau_xag_relative_value_v0 | PASS | 12.9567 | 0.0002 | 1.0100 |

## Interpretation

A PASS means breakout_retest remains the family winner after a block-bootstrap adjustment for multiple tested expert candidates. This is statistical support only; it does not remove the need for Phase 1 soak completion, Phase 2 paper trading, or live drift monitoring.

Summary rows are written to `outputs/reports/PHASE0_REALITY_CHECK_SUMMARY.csv`.
