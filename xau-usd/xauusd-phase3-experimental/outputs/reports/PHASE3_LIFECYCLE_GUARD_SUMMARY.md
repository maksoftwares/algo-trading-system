# Phase 3 Guarded Lifecycle Side Experiment

This report has no authority over Phase 2 readiness. PHASE2_READINESS_REPORT.md remains the sole real readiness authority.

Overall status: SIDE_EXPERIMENT_GUARDED_LIFECYCLE_READY

## Boundary

- This is a repo-only controller-design experiment.
- It compares guarded synthetic exposure against the harsh lifecycle stress model.
- Real Phase 2 readiness is not modified.
- MT5 runtime is not touched.
- Broker-action code is not allowed.
- `demo_authorized` remains `false` in every output row.

## Guard Rules

| Field | Value |
| --- | --- |
| Max proxy cost R | 0.3 |
| Daily lock R | -2.0 |
| Portfolio drawdown lock R | -4.0 |
| Worst-case budget check | blocks if a new -1R minus cost outcome would breach daily or portfolio limits |
| Cost-watch rows | blocked before synthetic exposure |
| No-exposure rows | kept review-only |

## A/B Summary

| Field | Value |
| --- | --- |
| Baseline opens | 53 |
| Guarded opens | 3 |
| Blocked rows | 50 |
| Baseline total net R | -10.9699 |
| Guarded total net R | -3.5803 |
| Net improvement R | 7.3896 |
| Baseline max DD R | -12.4405 |
| Guarded max DD R | -3.5803 |
| Drawdown improvement R | 8.8602 |
| Guarded win rate pct | 0.0 |
| Demo authorized | False |

## Guard Decision Counts

| Field | Value |
| --- | --- |
| BLOCKED_COST_R | 3 |
| BLOCKED_COST_WATCH | 2 |
| BLOCKED_DAILY_BUDGET | 20 |
| BLOCKED_PORTFOLIO_BUDGET | 25 |
| GUARDED_SYNTHETIC_OPEN | 3 |
| NO_EXPOSURE_REVIEW_ONLY | 63 |

## Block Reason Counts

| Field | Value |
| --- | --- |
| baseline_no_exposure | 63 |
| blank | 3 |
| cost_watch_requires_review_before_exposure | 2 |
| daily_worst_case_loss_budget_would_breach | 20 |
| portfolio_worst_case_loss_budget_would_breach | 25 |
| proxy_cost_r_at_or_above_0_30 | 3 |

## Sample Rows

| guard_event_id | source_cluster_id | decision_bar_time | input_paper_shadow_action | baseline_synthetic_net_r | guard_decision | guard_block_reason | guarded_synthetic_net_r | guarded_running_drawdown_r | daily_lock_active_after_event | portfolio_lock_active_after_event |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PH3GUARD00001 | WS001 | 2026.05.22 11:25:00 | WOULD_PAPER_SHADOW_OPEN | -1.2529 | GUARDED_SYNTHETIC_OPEN |  | -1.2529 | -1.2529 | false | false |
| PH3GUARD00002 | WS002 | 2026.05.22 11:25:00 | NO_EXPOSURE_DUPLICATE_IGNORED | 0.0000 | NO_EXPOSURE_REVIEW_ONLY | baseline_no_exposure | 0.0000 | -1.2529 | false | false |
| PH3GUARD00003 | WS003 | 2026.05.22 11:50:00 | WOULD_PAPER_SHADOW_OPEN | 0.1769 | BLOCKED_DAILY_BUDGET | daily_worst_case_loss_budget_would_breach | 0.0000 | -1.2529 | false | false |
| PH3GUARD00004 | WS004 | 2026.05.22 11:50:00 | NO_EXPOSURE_DUPLICATE_IGNORED | 0.0000 | NO_EXPOSURE_REVIEW_ONLY | baseline_no_exposure | 0.0000 | -1.2529 | false | false |
| PH3GUARD00005 | WS005 | 2026.05.22 12:45:00 | BLOCKED_SUSPEND_FAMILY | 0.0000 | NO_EXPOSURE_REVIEW_ONLY | baseline_no_exposure | 0.0000 | -1.2529 | false | false |
| PH3GUARD00006 | WS006 | 2026.05.22 12:45:00 | NO_EXPOSURE_DUPLICATE_IGNORED | 0.0000 | NO_EXPOSURE_REVIEW_ONLY | baseline_no_exposure | 0.0000 | -1.2529 | false | false |
| PH3GUARD00007 | WS007 | 2026.05.22 12:50:00 | WOULD_PAPER_SHADOW_OPEN | -0.2633 | BLOCKED_DAILY_BUDGET | daily_worst_case_loss_budget_would_breach | 0.0000 | -1.2529 | false | false |
| PH3GUARD00008 | WS008 | 2026.05.22 12:50:00 | NO_EXPOSURE_DUPLICATE_IGNORED | 0.0000 | NO_EXPOSURE_REVIEW_ONLY | baseline_no_exposure | 0.0000 | -1.2529 | false | false |
| PH3GUARD00009 | WS009 | 2026.05.22 14:05:00 | WOULD_PAPER_SHADOW_OPEN | -0.4363 | BLOCKED_DAILY_BUDGET | daily_worst_case_loss_budget_would_breach | 0.0000 | -1.2529 | false | false |
| PH3GUARD00010 | WS010 | 2026.05.22 14:05:00 | NO_EXPOSURE_DUPLICATE_IGNORED | 0.0000 | NO_EXPOSURE_REVIEW_ONLY | baseline_no_exposure | 0.0000 | -1.2529 | false | false |
| PH3GUARD00011 | WS011 | 2026.05.25 05:50:00 | WOULD_PAPER_SHADOW_OPEN | -1.1838 | GUARDED_SYNTHETIC_OPEN |  | -1.1838 | -2.4367 | false | false |
| PH3GUARD00012 | WS012 | 2026.05.25 05:50:00 | NO_EXPOSURE_DUPLICATE_IGNORED | 0.0000 | NO_EXPOSURE_REVIEW_ONLY | baseline_no_exposure | 0.0000 | -2.4367 | false | false |
