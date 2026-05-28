# Phase 3 Suspend Family Decision

This report has no authority over Phase 2 readiness. PHASE2_READINESS_REPORT.md remains the sole real readiness authority.

Overall status: REVIEW_READY_KEEP_SUSPENDED

## Summary

| Field | Value |
| --- | --- |
| Raw suspend rows | 22 |
| Primary suspend rows | 12 |
| Unique family events | 12 |
| Decision counts | {'KEEP_SUSPENDED': 12} |
| Suggested annotation counts | {'COST_ISSUE': 6, 'TIGHT_STOP_ISSUE': 4, 'UNKNOWN': 2} |
| Future rule counts | {'REQUIRE_COST_R_AND_SPREAD_BLOCK': 6, 'REQUIRE_MANUAL_REVIEW_BEFORE_PROMOTION': 2, 'REQUIRE_TIGHT_STOP_COST_BLOCK': 4} |

## Decision

All primary suspended family events remain `KEEP_SUSPENDED` in the future design. This is not owner approval and does not authorize paper-mode execution. It only converts the current cost-survival evidence into explicit future implementation requirements.

## Primary Suspended Events

| family_event_id | primary_event_id | decision_bar_time | direction | measured_cost_r_proxy | net_after_proxy_from_gross_r | diagnosis | suggested_reviewer_annotation | codex_review_decision | future_rule |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FAM00003 | PH3EXP00005 | 2026.05.22 12:45:00 | LONG | 0.3734 | 0.1382 | wide_spread_plus_entry_exit_cost | COST_ISSUE | KEEP_SUSPENDED | REQUIRE_COST_R_AND_SPREAD_BLOCK |
| FAM00008 | PH3EXP00015 | 2026.05.25 12:50:00 | SHORT | 0.4804 | 0.0312 | wide_spread_plus_entry_exit_cost | COST_ISSUE | KEEP_SUSPENDED | REQUIRE_COST_R_AND_SPREAD_BLOCK |
| FAM00010 | PH3EXP00019 | 2026.05.25 15:05:00 | LONG | 0.5735 | -0.0619 | tight_stop_cost_dominates | TIGHT_STOP_ISSUE | KEEP_SUSPENDED | REQUIRE_TIGHT_STOP_COST_BLOCK |
| FAM00011 | PH3EXP00021 | 2026.05.25 15:15:00 | LONG | 0.5652 | -0.0536 | wide_spread_plus_entry_exit_cost | COST_ISSUE | KEEP_SUSPENDED | REQUIRE_COST_R_AND_SPREAD_BLOCK |
| FAM00012 | PH3EXP00023 | 2026.05.25 16:45:00 | LONG | 0.6213 | -0.1097 | tight_stop_cost_dominates | TIGHT_STOP_ISSUE | KEEP_SUSPENDED | REQUIRE_TIGHT_STOP_COST_BLOCK |
| FAM00013 | PH3EXP00025 | 2026.05.25 16:50:00 | LONG | 0.4801 | 0.0315 | normal_spread_small_stop | UNKNOWN | KEEP_SUSPENDED | REQUIRE_MANUAL_REVIEW_BEFORE_PROMOTION |
| FAM00014 | PH3EXP00027 | 2026.05.25 22:20:00 | LONG | 0.4822 | 0.0294 | normal_spread_small_stop | UNKNOWN | KEEP_SUSPENDED | REQUIRE_MANUAL_REVIEW_BEFORE_PROMOTION |
| FAM00034 | PH3EXP00066 | 2026.05.27 06:05:00 | SHORT | 0.3867 | 0.1249 | wide_spread_plus_entry_exit_cost | COST_ISSUE | KEEP_SUSPENDED | REQUIRE_COST_R_AND_SPREAD_BLOCK |
| FAM00039 | PH3EXP00075 | 2026.05.27 09:55:00 | LONG | 0.5197 | -0.0081 | tight_stop_cost_dominates | TIGHT_STOP_ISSUE | KEEP_SUSPENDED | REQUIRE_TIGHT_STOP_COST_BLOCK |
| FAM00046 | PH3EXP00086 | 2026.05.27 18:00:00 | SHORT | 0.4639 | 0.0477 | wide_spread_plus_entry_exit_cost | COST_ISSUE | KEEP_SUSPENDED | REQUIRE_COST_R_AND_SPREAD_BLOCK |
| FAM00049 | PH3EXP00089 | 2026.05.27 19:55:00 | SHORT | 0.5228 | -0.0112 | tight_stop_cost_dominates | TIGHT_STOP_ISSUE | KEEP_SUSPENDED | REQUIRE_TIGHT_STOP_COST_BLOCK |
| FAM00061 | PH3EXP00107 | 2026.05.28 11:25:00 | SHORT | 0.3631 | 0.1485 | wide_spread_plus_entry_exit_cost | COST_ISSUE | KEEP_SUSPENDED | REQUIRE_COST_R_AND_SPREAD_BLOCK |
