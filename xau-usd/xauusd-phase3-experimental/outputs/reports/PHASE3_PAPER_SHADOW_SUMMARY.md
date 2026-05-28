# Phase 3 Paper-Shadow Side Experiment

This report has no authority over Phase 2 readiness. PHASE2_READINESS_REPORT.md remains the sole real readiness authority.

Overall status: SIDE_EXPERIMENT_PAPER_SHADOW_READY_WITH_COST_BLOCKS

## Boundary

- This is a repo-only side experiment.
- Real Phase 2 readiness is read as context and is not modified.
- MT5 runtime is not touched.
- Broker-action code is not allowed.
- `demo_authorized` remains `false` in every output row.

## Summary

| Field | Value |
| --- | --- |
| Real Phase 2 readiness | PENDING |
| Source ledger rows | 116 |
| Primary stream rows | 65 |
| Would shadow-open | 53 |
| Would shadow-open with cost review | 2 |
| Blocked by suspend-family rule | 12 |
| Observer no-exposure rows | 51 |
| Duplicate ignored | 51 |
| Conflict review | 0 |
| Estimated monthly shadow opens | 263.17 |
| Mean shadow-open net R | 0.299 |
| Demo authorized | False |
| Boundary | side_experiment_only_no_mt5_touch_no_real_gate_promotion |

## Action Counts

| Field | Value |
| --- | --- |
| BLOCKED_SUSPEND_FAMILY | 12 |
| NO_EXPOSURE_DUPLICATE_IGNORED | 51 |
| WOULD_PAPER_SHADOW_OPEN | 51 |
| WOULD_PAPER_SHADOW_OPEN_REVIEW | 2 |

## State Counts

| Field | Value |
| --- | --- |
| COST_WATCH_OPEN_WITH_REVIEW | 2 |
| DUPLICATE_IGNORED | 51 |
| PAPER_SHADOW_ELIGIBLE | 51 |
| SUSPEND_FAMILY_BLOCKED | 12 |

## Sample Rows

| paper_shadow_event_id | source_cluster_id | family_event_id | family_event_role | observer | decision_bar_time | direction | kill_rule_state | paper_shadow_state | paper_shadow_action | proxy_cost_r | net_after_proxy_from_gross_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PH3SHADOW00001 | WS001 | FAM00001 | PRIMARY_EXECUTION_CANDIDATE | breakout_retest | 2026.05.22 11:25:00 | SHORT | NORMAL | PAPER_SHADOW_ELIGIBLE | WOULD_PAPER_SHADOW_OPEN | 0.2529 | 0.2587 |
| PH3SHADOW00002 | WS002 | FAM00001 | OBSERVER_DUPLICATE | swing_breakout_retest_v0 | 2026.05.22 11:25:00 | SHORT | NORMAL | DUPLICATE_IGNORED | NO_EXPOSURE_DUPLICATE_IGNORED | 0.2529 | 0.2587 |
| PH3SHADOW00003 | WS003 | FAM00002 | PRIMARY_EXECUTION_CANDIDATE | breakout_retest | 2026.05.22 11:50:00 | LONG | NORMAL | PAPER_SHADOW_ELIGIBLE | WOULD_PAPER_SHADOW_OPEN | 0.1731 | 0.3385 |
| PH3SHADOW00004 | WS004 | FAM00002 | OBSERVER_DUPLICATE | swing_breakout_retest_v0 | 2026.05.22 11:50:00 | LONG | NORMAL | DUPLICATE_IGNORED | NO_EXPOSURE_DUPLICATE_IGNORED | 0.1731 | 0.3385 |
| PH3SHADOW00005 | WS005 | FAM00003 | PRIMARY_EXECUTION_CANDIDATE | breakout_retest | 2026.05.22 12:45:00 | LONG | SUSPEND_FAMILY | SUSPEND_FAMILY_BLOCKED | BLOCKED_SUSPEND_FAMILY | 0.3734 | 0.1382 |
| PH3SHADOW00006 | WS006 | FAM00003 | OBSERVER_DUPLICATE | swing_breakout_retest_v0 | 2026.05.22 12:45:00 | LONG | SUSPEND_FAMILY | DUPLICATE_IGNORED | NO_EXPOSURE_DUPLICATE_IGNORED | 0.3734 | 0.1382 |
| PH3SHADOW00007 | WS007 | FAM00004 | PRIMARY_EXECUTION_CANDIDATE | breakout_retest | 2026.05.22 12:50:00 | LONG | NORMAL | PAPER_SHADOW_ELIGIBLE | WOULD_PAPER_SHADOW_OPEN | 0.2633 | 0.2483 |
| PH3SHADOW00008 | WS008 | FAM00004 | OBSERVER_DUPLICATE | swing_breakout_retest_v0 | 2026.05.22 12:50:00 | LONG | NORMAL | DUPLICATE_IGNORED | NO_EXPOSURE_DUPLICATE_IGNORED | 0.2633 | 0.2483 |
| PH3SHADOW00009 | WS009 | FAM00005 | PRIMARY_EXECUTION_CANDIDATE | breakout_retest | 2026.05.22 14:05:00 | SHORT | NORMAL | PAPER_SHADOW_ELIGIBLE | WOULD_PAPER_SHADOW_OPEN | 0.1863 | 0.3253 |
| PH3SHADOW00010 | WS010 | FAM00005 | OBSERVER_DUPLICATE | swing_breakout_retest_v0 | 2026.05.22 14:05:00 | SHORT | NORMAL | DUPLICATE_IGNORED | NO_EXPOSURE_DUPLICATE_IGNORED | 0.1863 | 0.3253 |
| PH3SHADOW00011 | WS011 | FAM00006 | PRIMARY_EXECUTION_CANDIDATE | breakout_retest | 2026.05.25 05:50:00 | SHORT | NORMAL | PAPER_SHADOW_ELIGIBLE | WOULD_PAPER_SHADOW_OPEN | 0.1838 | 0.3278 |
| PH3SHADOW00012 | WS012 | FAM00006 | OBSERVER_DUPLICATE | swing_breakout_retest_v0 | 2026.05.25 05:50:00 | SHORT | NORMAL | DUPLICATE_IGNORED | NO_EXPOSURE_DUPLICATE_IGNORED | 0.1838 | 0.3278 |
