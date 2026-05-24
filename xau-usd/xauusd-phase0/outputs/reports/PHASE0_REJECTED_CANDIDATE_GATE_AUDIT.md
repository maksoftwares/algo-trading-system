# Phase 0 Rejected Candidate Gate Audit

Generated at UTC: `2026-05-24T09:37:39+00:00`

Purpose: answer Review #3 V3 by aggregating the matrix gates that rejected candidate experts.

Approved/same-family rows are included for context but excluded from the rejection counts.

Approved or active experts excluded from rejection counts: `breakout_retest, swing_breakout_retest_v0, symbol_normalized_round_retest_v0`

## Summary

- Audited candidates: 38
- Rejected/research candidates audited: 35
- Rejected candidates with sample-size failure: 8
- Rejected candidates with multi-cell expectancy failure: 33
- Rejected candidates with both expectancy and sample-size failure: 8
- Rejected candidates with expectancy-only failure: 25
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
| d1_compression_h4_expansion_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 783 | 68 | multi_cell_survival;concentration |
| d1_inside_day_breakout_v0 | REJECTED_OR_RESEARCH | EDGE_AND_FREQUENCY_FAILURE | 9 | 3 | 192 | 11 | multi_cell_survival;sample_size;concentration;activity |
| d1_momentum_h4_pullback_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 3 | 684 | 69 | multi_cell_survival;concentration |
| d1_multi_day_exhaustion_reversion_v0 | REJECTED_OR_RESEARCH | EDGE_AND_FREQUENCY_FAILURE | 9 | 0 | 291 | 24 | multi_cell_survival;sample_size;concentration;activity |
| d1_outside_day_followthrough_v0 | REJECTED_OR_RESEARCH | EDGE_AND_FREQUENCY_FAILURE | 9 | 0 | 261 | 22 | multi_cell_survival;sample_size;concentration;activity |
| d1_volatility_expansion_reversal_v0 | REJECTED_OR_RESEARCH | EDGE_AND_FREQUENCY_FAILURE | 9 | 0 | 354 | 30 | multi_cell_survival;sample_size;concentration |
| daily_pivot_reclaim_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 4713 | 486 | multi_cell_survival;no_catastrophic_failure;concentration |
| emr_inactivity_long_v0 | REJECTED_OR_RESEARCH | EDGE_AND_FREQUENCY_FAILURE | 9 | 0 | 84 | 9 | multi_cell_survival;sample_size;concentration;activity |
| extreme_activity_mean_reversion_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 1056 | 74 | multi_cell_survival;concentration |
| h4_d1_momentum_expansion_continuation_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 3 | 735 | 81 | multi_cell_survival;concentration |
| h4_inside_bar_d1_momentum_breakout_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 2 | 741 | 71 | multi_cell_survival;concentration |
| liquidity_sweep_continuation_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 12222 | 1281 | multi_cell_survival;no_catastrophic_failure;concentration |
| liquidity_sweep_reversal_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 3906 | 393 | multi_cell_survival;no_catastrophic_failure;concentration |
| london_fix_continuation_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 4821 | 463 | multi_cell_survival;concentration |
| m15_inside_bar_breakout_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 7170 | 727 | multi_cell_survival;concentration |
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

## Gate Columns

- `multi_cell_survival`: PF persistence across the 9-cell matrix.
- `sample_size`: minimum trades in every cell.
- `no_catastrophic_failure`: drawdown and total-return loss limits.
- `concentration`: single/top-5 trade contribution limits.
- `activity`: zero-trade month limit.
- `cost_sensitivity`: P95 PF divided by best-case PF.
