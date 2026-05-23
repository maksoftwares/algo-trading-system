# PHASE0 REALITY CHECK

Status: PASS
Generated at UTC: 2026-05-23T18:03:50+00:00
Approved expert under test: breakout_retest

## Method

This report applies a White Reality Check and SPA-style pairwise bootstrap to monthly fixed-notional R returns for the Phase 0 expert family. Each expert's monthly value is the average monthly R sum across its matrix trade ledgers, which keeps cost/broker cells from turning into separate optimized candidates and avoids compounding-dollar scale artifacts.

- Bootstrap iterations: 5000
- Circular block length: 3 month(s)
- Maximum accepted p-value: 0.1
- Effective accepted p-value: 0.1
- Candidate universes with at least 30 non-empty matrix-ledger candidates are tightened to alpha = 0.01.
- Months in panel: 108

## White Reality Check

| Winner | White p | q90 R | q95 R | q99 R |
| --- | --- | --- | --- | --- |
| breakout_retest | 0.0002 | 1.1378 | 1.3456 | 1.7720 |

## Expert Means

| Expert | Mean Monthly R | Total R | Role |
| --- | --- | --- | --- |
| asia_range_london_breakout_v0 | -0.6926 | -74.80 | alternative |
| asia_range_london_failed_break_reversal_v0 | -0.3749 | -40.49 | alternative |
| breakout_retest | 12.9666 | 1400.40 | approved |
| d1_momentum_h4_pullback_v0 | 0.1090 | 11.77 | alternative |
| d1_volatility_expansion_reversal_v0 | -0.0029 | -0.32 | alternative |
| daily_pivot_reclaim_v0 | -0.2632 | -28.43 | alternative |
| emr_inactivity_long_v0 | 0.0022 | 0.24 | alternative |
| extreme_activity_mean_reversion_v0 | -0.1063 | -11.48 | alternative |
| liquidity_sweep_continuation_v0 | -0.9719 | -104.97 | alternative |
| liquidity_sweep_reversal_v0 | -0.5052 | -54.56 | alternative |
| london_fix_continuation_v0 | -0.1354 | -14.63 | alternative |
| m15_inside_bar_breakout_v0 | -0.0846 | -9.14 | alternative |
| m5_impulse_continuation_v0 | -1.0317 | -111.42 | alternative |
| ny_am_pullback_continuation_v0 | -0.1281 | -13.84 | alternative |
| ny_failed_london_reversal_v0 | -0.0398 | -4.30 | alternative |
| ny_london_overlap_compression_break_v0 | -0.0100 | -1.08 | alternative |
| opening_drive_failed_continuation_v0 | -0.1762 | -19.03 | alternative |
| post_spike_short_v0 | -0.0660 | -7.12 | alternative |
| previous_day_extreme_retest_v0 | -0.1903 | -20.55 | alternative |
| range_mr | -0.0375 | -4.05 | alternative |
| round_number_retest_v0 | 11.0507 | 1193.48 | alternative |
| session_extreme_retest_v0 | 5.4747 | 591.27 | alternative |
| session_vwap_reclaim_v0 | -0.3606 | -38.95 | alternative |
| squeeze_breakout_long_v0 | 0.0374 | 4.03 | alternative |
| swing_breakout_retest_v0 | 11.2019 | 1209.81 | alternative |
| symbol_normalized_round_retest_v0 | 11.0507 | 1193.48 | alternative |
| symbol_round_sweep_reversal_v0 | -0.6750 | -72.90 | alternative |
| trend_pullback | -1.8156 | -196.08 | alternative |
| weekly_level_reclaim_v0 | -0.0925 | -9.99 | alternative |

## SPA-Style Pairwise Checks

| Alternative | Status | Mean Edge R | SPA p | Bootstrap q95 R |
| --- | --- | --- | --- | --- |
| asia_range_london_breakout_v0 | PASS | 13.6592 | 0.0002 | 1.0179 |
| asia_range_london_failed_break_reversal_v0 | PASS | 13.3415 | 0.0002 | 1.0531 |
| d1_momentum_h4_pullback_v0 | PASS | 12.8577 | 0.0002 | 1.0440 |
| d1_volatility_expansion_reversal_v0 | PASS | 12.9696 | 0.0002 | 1.0102 |
| daily_pivot_reclaim_v0 | PASS | 13.2298 | 0.0002 | 1.0222 |
| emr_inactivity_long_v0 | PASS | 12.9644 | 0.0002 | 0.9793 |
| extreme_activity_mean_reversion_v0 | PASS | 13.0730 | 0.0002 | 0.9840 |
| liquidity_sweep_continuation_v0 | PASS | 13.9385 | 0.0002 | 1.0913 |
| liquidity_sweep_reversal_v0 | PASS | 13.4718 | 0.0002 | 1.0011 |
| london_fix_continuation_v0 | PASS | 13.1021 | 0.0002 | 1.0258 |
| m15_inside_bar_breakout_v0 | PASS | 13.0512 | 0.0002 | 1.0277 |
| m5_impulse_continuation_v0 | PASS | 13.9983 | 0.0002 | 1.0041 |
| ny_am_pullback_continuation_v0 | PASS | 13.0947 | 0.0002 | 0.9851 |
| ny_failed_london_reversal_v0 | PASS | 13.0064 | 0.0002 | 1.0352 |
| ny_london_overlap_compression_break_v0 | PASS | 12.9767 | 0.0002 | 0.9955 |
| opening_drive_failed_continuation_v0 | PASS | 13.1428 | 0.0002 | 1.0285 |
| post_spike_short_v0 | PASS | 13.0326 | 0.0002 | 1.0159 |
| previous_day_extreme_retest_v0 | PASS | 13.1569 | 0.0002 | 1.0062 |
| range_mr | PASS | 13.0041 | 0.0002 | 1.0027 |
| round_number_retest_v0 | PASS | 1.9159 | 0.0188 | 1.5106 |
| session_extreme_retest_v0 | PASS | 7.4919 | 0.0002 | 1.0863 |
| session_vwap_reclaim_v0 | PASS | 13.3272 | 0.0002 | 0.9767 |
| squeeze_breakout_long_v0 | PASS | 12.9293 | 0.0002 | 1.0254 |
| swing_breakout_retest_v0 | PASS | 1.7647 | 0.0002 | 0.3909 |
| symbol_normalized_round_retest_v0 | PASS | 1.9159 | 0.0148 | 1.4732 |
| symbol_round_sweep_reversal_v0 | PASS | 13.6416 | 0.0002 | 1.0448 |
| trend_pullback | PASS | 14.7822 | 0.0002 | 1.1620 |
| weekly_level_reclaim_v0 | PASS | 13.0592 | 0.0002 | 1.0079 |

## Interpretation

A PASS means breakout_retest remains the family winner after a block-bootstrap adjustment for multiple tested expert candidates. This is statistical support only; it does not remove the need for Phase 1 soak completion, Phase 2 paper trading, or live drift monitoring.

Summary rows are written to `outputs/reports/PHASE0_REALITY_CHECK_SUMMARY.csv`.
