# Phase 3 Suspend Family Review

This report has no authority over Phase 2 readiness. PHASE2_READINESS_REPORT.md remains the sole real readiness authority.

Overall status: REVIEW_READY

## Summary

| Field | Value |
| --- | --- |
| Raw ledger rows | 116 |
| Suspend raw rows | 22 |
| Suspend unique family events | 12 |
| Suspend primary rows | 12 |
| Suspend duplicate observer rows | 10 |
| Gross expectancy R source | fixed_notional_phase0_baseline |
| Baseline assumed cost R | 0.3228 |
| Baseline net expectancy R | 0.1888 |
| Max cost proxy R before suspend | 0.3616 |
| Median suspend cost R | 0.4813 |
| Median suspend net delta vs assumed baseline R | -0.1585 |
| Median suspend stop distance points | 256.105 |

## Cost Semantics

Suspension rows are identified from baseline gross expectancy minus the Phase 3 proxy cost. The delta column is the proxy-based net minus the Phase 0 assumed-cost baseline net; it is a design stress signal, not Phase 2 readiness evidence.

## Diagnosis Counts

| Field | Value |
| --- | --- |
| normal_spread_small_stop | 4 |
| tight_stop_cost_dominates | 7 |
| wide_spread_plus_entry_exit_cost | 11 |

## Reviewer Annotation Template

| Field | Value |
| --- | --- |
| COST_ISSUE | Spread/slippage proxy dominates an otherwise mechanically valid event. |
| TIGHT_STOP_ISSUE | Stop distance is so small that normal cost consumes the edge. |
| TIMING_ISSUE | Event timing appears structurally poor even before cost. |
| DUPLICATED_OBSERVER_ISSUE | Suspension belongs to a duplicate observer row, not a primary event. |
| UNKNOWN | Reviewer could not classify the suspension with current evidence. |

## Suggested Annotation Counts

| Field | Value |
| --- | --- |
| COST_ISSUE | 6 |
| DUPLICATED_OBSERVER_ISSUE | 10 |
| TIGHT_STOP_ISSUE | 4 |
| UNKNOWN | 2 |

## Role Counts

| Field | Value |
| --- | --- |
| OBSERVER_DUPLICATE | 10 |
| PRIMARY_EXECUTION_CANDIDATE | 12 |

## Highest Cost Suspensions

| event_id | family_event_id | family_event_role | observer | decision_bar_time | direction | total_cost_points | stop_distance_points | measured_cost_r_proxy | net_delta_vs_assumed_baseline_r | cost_excess_r | diagnosis | suggested_reviewer_annotation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PH3EXP00023 | FAM00012 | PRIMARY_EXECUTION_CANDIDATE | breakout_retest | 2026.05.25 16:45:00 | LONG | 110.0000 | 177.0400 | 0.6213 | -0.2985 | 0.2597 | tight_stop_cost_dominates | TIGHT_STOP_ISSUE |
| PH3EXP00024 | FAM00012 | OBSERVER_DUPLICATE | swing_breakout_retest_v0 | 2026.05.25 16:45:00 | LONG | 110.0000 | 177.0400 | 0.6213 | -0.2985 | 0.2597 | tight_stop_cost_dominates | DUPLICATED_OBSERVER_ISSUE |
| PH3EXP00019 | FAM00010 | PRIMARY_EXECUTION_CANDIDATE | breakout_retest | 2026.05.25 15:05:00 | LONG | 110.0000 | 191.8100 | 0.5735 | -0.2507 | 0.2119 | tight_stop_cost_dominates | TIGHT_STOP_ISSUE |
| PH3EXP00020 | FAM00010 | OBSERVER_DUPLICATE | swing_breakout_retest_v0 | 2026.05.25 15:05:00 | LONG | 110.0000 | 191.8100 | 0.5735 | -0.2507 | 0.2119 | tight_stop_cost_dominates | DUPLICATED_OBSERVER_ISSUE |
| PH3EXP00021 | FAM00011 | PRIMARY_EXECUTION_CANDIDATE | breakout_retest | 2026.05.25 15:15:00 | LONG | 160.0000 | 283.0900 | 0.5652 | -0.2424 | 0.2036 | wide_spread_plus_entry_exit_cost | COST_ISSUE |
| PH3EXP00022 | FAM00011 | OBSERVER_DUPLICATE | swing_breakout_retest_v0 | 2026.05.25 15:15:00 | LONG | 160.0000 | 283.0900 | 0.5652 | -0.2424 | 0.2036 | wide_spread_plus_entry_exit_cost | DUPLICATED_OBSERVER_ISSUE |
| PH3EXP00089 | FAM00049 | PRIMARY_EXECUTION_CANDIDATE | breakout_retest | 2026.05.27 19:55:00 | SHORT | 110.0000 | 210.4200 | 0.5228 | -0.2000 | 0.1612 | tight_stop_cost_dominates | TIGHT_STOP_ISSUE |
| PH3EXP00075 | FAM00039 | PRIMARY_EXECUTION_CANDIDATE | breakout_retest | 2026.05.27 09:55:00 | LONG | 110.0000 | 211.6700 | 0.5197 | -0.1969 | 0.1581 | tight_stop_cost_dominates | TIGHT_STOP_ISSUE |
| PH3EXP00076 | FAM00039 | OBSERVER_DUPLICATE | swing_breakout_retest_v0 | 2026.05.27 09:55:00 | LONG | 110.0000 | 211.6700 | 0.5197 | -0.1969 | 0.1581 | tight_stop_cost_dominates | DUPLICATED_OBSERVER_ISSUE |
| PH3EXP00027 | FAM00014 | PRIMARY_EXECUTION_CANDIDATE | breakout_retest | 2026.05.25 22:20:00 | LONG | 110.0000 | 228.1100 | 0.4822 | -0.1594 | 0.1206 | normal_spread_small_stop | UNKNOWN |
| PH3EXP00028 | FAM00014 | OBSERVER_DUPLICATE | swing_breakout_retest_v0 | 2026.05.25 22:20:00 | LONG | 110.0000 | 228.1100 | 0.4822 | -0.1594 | 0.1206 | normal_spread_small_stop | DUPLICATED_OBSERVER_ISSUE |
| PH3EXP00015 | FAM00008 | PRIMARY_EXECUTION_CANDIDATE | breakout_retest | 2026.05.25 12:50:00 | SHORT | 160.0000 | 333.0400 | 0.4804 | -0.1576 | 0.1188 | wide_spread_plus_entry_exit_cost | COST_ISSUE |

## Recommendation

Do not promote these rows into real execution. If Phase 2 later passes, use this review to require cost-aware entry blocking before any paper-mode order path is considered.
