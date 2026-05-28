# Phase 3 Demo Rehearsal Checklist

This report has no authority over Phase 2 readiness. PHASE2_READINESS_REPORT.md remains the sole real readiness authority.

Overall status: SIDE_EXPERIMENT_DEMO_REHEARSAL_READY

## Boundary

- This is a side-experiment demo rehearsal package.
- It does not start demo, paper, or live runtime activity.
- It does not touch MT5 runtime files.
- It does not authorize broker-side actions.
- `demo_authorized` and `can_start_real_demo` remain `false`.

## Rehearsal Summary

| Field | Value |
| --- | --- |
| Real Phase 2 readiness | PENDING |
| Source guard rows | 108 |
| Rehearsal events | 111 |
| Shadow open events | 3 |
| Shadow close events | 3 |
| Blocked events | 46 |
| Cost-block events | 5 |
| Risk-block events | 41 |
| No-exposure events | 59 |
| Guarded total net R | -3.5803 |
| Guarded max DD R | -3.5803 |
| Can start real demo | False |

## Required Before Real Demo

- real_phase2_readiness_pass
- owner_demo_start_approval
- separate_runtime_deployment_review

## Rehearsal Event Counts

| Field | Value |
| --- | --- |
| REHEARSAL_BLOCKED_COST | 5 |
| REHEARSAL_BLOCKED_RISK | 41 |
| REHEARSAL_NO_EXPOSURE | 59 |
| REHEARSAL_SHADOW_CLOSE | 3 |
| REHEARSAL_SHADOW_OPEN | 3 |

## Sample Rehearsal Rows

| rehearsal_event_id | source_cluster_id | decision_bar_time | guard_decision | rehearsal_event_type | rehearsal_action | synthetic_net_r | running_rehearsal_drawdown_r | can_start_real_demo |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PH3REHEARSAL00001 | WS001 | 2026.05.22 11:25:00 | GUARDED_SYNTHETIC_OPEN | REHEARSAL_SHADOW_OPEN | record_shadow_intent_without_broker_side_effect | 0.0000 | 0.0000 | false |
| PH3REHEARSAL00002 | WS001 | 2026.05.22 11:25:00 | GUARDED_SYNTHETIC_OPEN | REHEARSAL_SHADOW_CLOSE | record_shadow_close_synthetic_stop_hit | -1.2529 | -1.2529 | false |
| PH3REHEARSAL00003 | WS002 | 2026.05.22 11:25:00 | NO_EXPOSURE_REVIEW_ONLY | REHEARSAL_NO_EXPOSURE | record_review_only_no_exposure | 0.0000 | -1.2529 | false |
| PH3REHEARSAL00004 | WS003 | 2026.05.22 11:50:00 | BLOCKED_DAILY_BUDGET | REHEARSAL_BLOCKED_RISK | record_risk_block_and_no_exposure | 0.0000 | -1.2529 | false |
| PH3REHEARSAL00005 | WS004 | 2026.05.22 11:50:00 | NO_EXPOSURE_REVIEW_ONLY | REHEARSAL_NO_EXPOSURE | record_review_only_no_exposure | 0.0000 | -1.2529 | false |
| PH3REHEARSAL00006 | WS005 | 2026.05.22 12:45:00 | NO_EXPOSURE_REVIEW_ONLY | REHEARSAL_NO_EXPOSURE | record_review_only_no_exposure | 0.0000 | -1.2529 | false |
| PH3REHEARSAL00007 | WS006 | 2026.05.22 12:45:00 | NO_EXPOSURE_REVIEW_ONLY | REHEARSAL_NO_EXPOSURE | record_review_only_no_exposure | 0.0000 | -1.2529 | false |
| PH3REHEARSAL00008 | WS007 | 2026.05.22 12:50:00 | BLOCKED_DAILY_BUDGET | REHEARSAL_BLOCKED_RISK | record_risk_block_and_no_exposure | 0.0000 | -1.2529 | false |
| PH3REHEARSAL00009 | WS008 | 2026.05.22 12:50:00 | NO_EXPOSURE_REVIEW_ONLY | REHEARSAL_NO_EXPOSURE | record_review_only_no_exposure | 0.0000 | -1.2529 | false |
| PH3REHEARSAL00010 | WS009 | 2026.05.22 14:05:00 | BLOCKED_DAILY_BUDGET | REHEARSAL_BLOCKED_RISK | record_risk_block_and_no_exposure | 0.0000 | -1.2529 | false |
| PH3REHEARSAL00011 | WS010 | 2026.05.22 14:05:00 | NO_EXPOSURE_REVIEW_ONLY | REHEARSAL_NO_EXPOSURE | record_review_only_no_exposure | 0.0000 | -1.2529 | false |
| PH3REHEARSAL00012 | WS011 | 2026.05.25 05:50:00 | GUARDED_SYNTHETIC_OPEN | REHEARSAL_SHADOW_OPEN | record_shadow_intent_without_broker_side_effect | 0.0000 | -1.2529 | false |
| PH3REHEARSAL00013 | WS011 | 2026.05.25 05:50:00 | GUARDED_SYNTHETIC_OPEN | REHEARSAL_SHADOW_CLOSE | record_shadow_close_synthetic_stop_hit | -1.1838 | -2.4367 | false |
| PH3REHEARSAL00014 | WS012 | 2026.05.25 05:50:00 | NO_EXPOSURE_REVIEW_ONLY | REHEARSAL_NO_EXPOSURE | record_review_only_no_exposure | 0.0000 | -2.4367 | false |
