# PHASE0 REALITY CHECK

Status: PASS
Generated at UTC: 2026-05-23T14:23:52+00:00
Approved expert under test: breakout_retest

## Method

This report applies a White Reality Check and SPA-style pairwise bootstrap to monthly trade-ledger returns for the Phase 0 expert family. Each expert's monthly value is the average monthly PnL across its matrix trade ledgers, which keeps cost/broker cells from turning into separate optimized candidates.

- Bootstrap iterations: 5000
- Circular block length: 3 month(s)
- Maximum accepted p-value: 0.1
- Months in panel: 108

## White Reality Check

| Winner | White p | q90 | q95 | q99 |
| --- | --- | --- | --- | --- |
| breakout_retest | 0.0200 | 120986.58 | 160688.48 | 250328.73 |

## Expert Means

| Expert | Mean Monthly PnL | Total PnL | Role |
| --- | --- | --- | --- |
| asia_range_london_breakout_v0 | -28.83 | -3113.24 | alternative |
| asia_range_london_failed_break_reversal_v0 | -16.89 | -1823.66 | alternative |
| breakout_retest | 209752.17 | 22653234.48 | approved |
| daily_pivot_reclaim_v0 | -11.41 | -1232.00 | alternative |
| emr_inactivity_long_v0 | 0.10 | 10.50 | alternative |
| extreme_activity_mean_reversion_v0 | -5.31 | -573.63 | alternative |
| liquidity_sweep_reversal_v0 | -21.76 | -2350.27 | alternative |
| london_fix_continuation_v0 | -7.05 | -761.12 | alternative |
| m15_inside_bar_breakout_v0 | -4.99 | -538.47 | alternative |
| m5_impulse_continuation_v0 | -38.61 | -4170.38 | alternative |
| ny_am_pullback_continuation_v0 | -6.65 | -717.72 | alternative |
| ny_failed_london_reversal_v0 | -2.39 | -258.64 | alternative |
| ny_london_overlap_compression_break_v0 | -0.52 | -56.31 | alternative |
| opening_drive_failed_continuation_v0 | -8.64 | -933.03 | alternative |
| post_spike_short_v0 | -3.46 | -373.49 | alternative |
| previous_day_extreme_retest_v0 | -9.14 | -987.22 | alternative |
| range_mr | -1.86 | -200.75 | alternative |
| session_vwap_reclaim_v0 | -16.87 | -1822.46 | alternative |
| squeeze_breakout_long_v0 | 1.77 | 191.43 | alternative |
| swing_breakout_retest_v0 | 52707.87 | 5692449.56 | alternative |
| trend_pullback | -51.37 | -5547.92 | alternative |
| weekly_level_reclaim_v0 | -4.63 | -499.71 | alternative |

## SPA-Style Pairwise Checks

| Alternative | Status | Mean Edge | SPA p | Bootstrap q95 |
| --- | --- | --- | --- | --- |
| asia_range_london_breakout_v0 | PASS | 209781.00 | 0.0234 | 166854.30 |
| asia_range_london_failed_break_reversal_v0 | PASS | 209769.06 | 0.0208 | 166350.70 |
| daily_pivot_reclaim_v0 | PASS | 209763.58 | 0.0230 | 164252.83 |
| emr_inactivity_long_v0 | PASS | 209752.07 | 0.0224 | 160633.02 |
| extreme_activity_mean_reversion_v0 | PASS | 209757.48 | 0.0236 | 169064.51 |
| liquidity_sweep_reversal_v0 | PASS | 209773.93 | 0.0184 | 154889.14 |
| london_fix_continuation_v0 | PASS | 209759.22 | 0.0190 | 159141.26 |
| m15_inside_bar_breakout_v0 | PASS | 209757.16 | 0.0230 | 167442.52 |
| m5_impulse_continuation_v0 | PASS | 209790.79 | 0.0206 | 163621.61 |
| ny_am_pullback_continuation_v0 | PASS | 209758.82 | 0.0194 | 161531.37 |
| ny_failed_london_reversal_v0 | PASS | 209754.57 | 0.0194 | 161115.30 |
| ny_london_overlap_compression_break_v0 | PASS | 209752.69 | 0.0222 | 164784.96 |
| opening_drive_failed_continuation_v0 | PASS | 209760.81 | 0.0238 | 166389.59 |
| post_spike_short_v0 | PASS | 209755.63 | 0.0194 | 160311.66 |
| previous_day_extreme_retest_v0 | PASS | 209761.31 | 0.0256 | 165659.67 |
| range_mr | PASS | 209754.03 | 0.0230 | 167306.60 |
| session_vwap_reclaim_v0 | PASS | 209769.05 | 0.0236 | 167315.06 |
| squeeze_breakout_long_v0 | PASS | 209750.40 | 0.0240 | 162452.98 |
| swing_breakout_retest_v0 | PASS | 157044.30 | 0.0264 | 129493.57 |
| trend_pullback | PASS | 209803.54 | 0.0240 | 164125.16 |
| weekly_level_reclaim_v0 | PASS | 209756.80 | 0.0236 | 165055.76 |

## Interpretation

A PASS means breakout_retest remains the family winner after a block-bootstrap adjustment for multiple tested expert candidates. This is statistical support only; it does not remove the need for Phase 1 soak completion, Phase 2 paper trading, or live drift monitoring.

Summary rows are written to `outputs/reports/PHASE0_REALITY_CHECK_SUMMARY.csv`.
