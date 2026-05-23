# Phase 0 Rejected Candidate Gate Audit

Generated at UTC: `2026-05-23T13:59:57+00:00`

Purpose: answer Review #3 V3 by aggregating the matrix gates that rejected candidate experts.

Approved/same-family rows are included for context but excluded from the rejection counts.

Approved or active experts excluded from rejection counts: `breakout_retest, swing_breakout_retest_v0`

## Summary

- Audited candidates: 21
- Rejected/research candidates audited: 19
- Rejected candidates with sample-size failure: 4
- Rejected candidates with multi-cell expectancy failure: 19
- Rejected candidates with both expectancy and sample-size failure: 4
- Rejected candidates with expectancy-only failure: 15
- Rejected candidates with frequency-only failure: 0

Conclusion: Sample-size/frequency failures are present, so low-frequency candidates should not be rescued by assumption; however, expectancy survival failures are at least as common and must remain the primary rejection evidence.

## Candidate Gate Table

| Candidate | Scope | Diagnosis | Cells | PF cells | Trades | Min trades | Failed gates |
|---|---|---|---:|---:|---:|---:|---|
| breakout_retest | APPROVED_OR_ACTIVE | APPROVED_EDGE_FAMILY | 9 | 7 | 66759 | 7174 | none |
| swing_breakout_retest_v0 | APPROVED_OR_ACTIVE | APPROVED_EDGE_FAMILY | 9 | 7 | 57897 | 6281 | none |
| asia_range_london_breakout_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 4845 | 507 | multi_cell_survival;no_catastrophic_failure;concentration |
| asia_range_london_failed_break_reversal_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 3102 | 326 | multi_cell_survival;no_catastrophic_failure;concentration |
| compression_retest_continuation_v0 | REJECTED_OR_RESEARCH | EDGE_AND_FREQUENCY_FAILURE | 9 | 0 | 0 | 0 | multi_cell_survival;sample_size;concentration;activity;cost_sensitivity |
| daily_pivot_reclaim_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 4713 | 486 | multi_cell_survival;no_catastrophic_failure;concentration |
| emr_inactivity_long_v0 | REJECTED_OR_RESEARCH | EDGE_AND_FREQUENCY_FAILURE | 9 | 0 | 84 | 9 | multi_cell_survival;sample_size;concentration;activity |
| extreme_activity_mean_reversion_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 1056 | 74 | multi_cell_survival;concentration |
| liquidity_sweep_reversal_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 3906 | 393 | multi_cell_survival;no_catastrophic_failure;concentration |
| london_fix_continuation_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 4821 | 463 | multi_cell_survival;concentration |
| ny_am_pullback_continuation_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 3195 | 326 | multi_cell_survival;concentration |
| ny_failed_london_reversal_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 3369 | 322 | multi_cell_survival;concentration |
| ny_london_overlap_compression_break_v0 | REJECTED_OR_RESEARCH | EDGE_AND_FREQUENCY_FAILURE | 9 | 3 | 135 | 2 | multi_cell_survival;sample_size;concentration;activity;cost_sensitivity |
| opening_drive_failed_continuation_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 2208 | 221 | multi_cell_survival;concentration |
| post_spike_short_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 1860 | 192 | multi_cell_survival;concentration |
| previous_day_extreme_retest_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 5295 | 478 | multi_cell_survival;no_catastrophic_failure;concentration |
| range_mr | REJECTED_OR_RESEARCH | EDGE_AND_FREQUENCY_FAILURE | 9 | 0 | 24 | 0 | multi_cell_survival;sample_size;concentration;activity;cost_sensitivity |
| session_vwap_reclaim_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 4806 | 481 | multi_cell_survival;no_catastrophic_failure;concentration |
| squeeze_breakout_long_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 1800 | 194 | multi_cell_survival;concentration |
| trend_pullback | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 27576 | 2873 | multi_cell_survival;no_catastrophic_failure;concentration |
| weekly_level_reclaim_v0 | REJECTED_OR_RESEARCH | EDGE_EXPECTANCY_FAILURE | 9 | 0 | 1083 | 113 | multi_cell_survival;concentration |

## Gate Columns

- `multi_cell_survival`: PF persistence across the 9-cell matrix.
- `sample_size`: minimum trades in every cell.
- `no_catastrophic_failure`: drawdown and total-return loss limits.
- `concentration`: single/top-5 trade contribution limits.
- `activity`: zero-trade month limit.
- `cost_sensitivity`: P95 PF divided by best-case PF.
