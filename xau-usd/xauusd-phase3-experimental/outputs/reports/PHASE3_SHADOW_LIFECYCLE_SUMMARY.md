# Phase 3 Shadow Lifecycle Side Experiment

This report has no authority over Phase 2 readiness. PHASE2_READINESS_REPORT.md remains the sole real readiness authority.

Overall status: SIDE_EXPERIMENT_SYNTHETIC_LIFECYCLE_READY

## Boundary

- This is a repo-only synthetic lifecycle experiment.
- It is not a backtest and not paper trading.
- Real Phase 2 readiness is not modified.
- MT5 runtime is not touched.
- Broker-action code is not allowed.
- `demo_authorized` remains `false` in every output row.

## Summary

| Field | Value |
| --- | --- |
| Source shadow rows | 116 |
| Synthetic opens | 53 |
| Synthetic closes | 53 |
| No-exposure review-only rows | 63 |
| Synthetic win rate pct | 28.3 |
| Synthetic total gross R | 0.3 |
| Synthetic total net R | -10.9699 |
| Synthetic mean net R | -0.207 |
| Synthetic final equity R | -10.9699 |
| Synthetic max drawdown R | -12.4405 |
| Demo authorized | False |
| Boundary | side_experiment_only_synthetic_lifecycle_no_mt5_touch_no_real_gate_promotion |

## Lifecycle Stage Counts

| Field | Value |
| --- | --- |
| NO_EXPOSURE_REVIEW_ONLY | 63 |
| OPENED_THEN_CLOSED | 48 |
| OPENED_THEN_COST_DRIFT_CLOSED | 3 |
| OPENED_THEN_REVIEW_CLOSED | 2 |

## Close Reason Counts

| Field | Value |
| --- | --- |
| cost_drift_exit | 3 |
| cost_watch_review_exit | 2 |
| net_expectancy_below_minimum_after_proxy_cost | 12 |
| observer_duplicate | 51 |
| synthetic_break_even | 11 |
| synthetic_stop_hit | 11 |
| synthetic_target_hit | 7 |
| synthetic_time_stop_small_loss | 11 |
| synthetic_time_stop_small_win | 8 |

## Risk Lock Counts

| Field | Value |
| --- | --- |
| NORMAL | 28 |
| SYNTHETIC_DAILY_LOCK | 83 |
| SYNTHETIC_DEFENSIVE | 5 |

## Sample Rows

| lifecycle_event_id | paper_shadow_event_id | source_cluster_id | decision_bar_time | input_paper_shadow_action | lifecycle_stage | synthetic_close_reason | synthetic_hold_bars | synthetic_net_r | running_synthetic_equity_r | risk_lock_after_event |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PH3LIFE00001 | PH3SHADOW00001 | WS001 | 2026.05.22 11:25:00 | WOULD_PAPER_SHADOW_OPEN | OPENED_THEN_CLOSED | synthetic_stop_hit | 5 | -1.2529 | -1.2529 | NORMAL |
| PH3LIFE00002 | PH3SHADOW00002 | WS002 | 2026.05.22 11:25:00 | NO_EXPOSURE_DUPLICATE_IGNORED | NO_EXPOSURE_REVIEW_ONLY | observer_duplicate | 0 | 0.0000 | -1.2529 | NORMAL |
| PH3LIFE00003 | PH3SHADOW00003 | WS003 | 2026.05.22 11:50:00 | WOULD_PAPER_SHADOW_OPEN | OPENED_THEN_CLOSED | synthetic_time_stop_small_win | 12 | 0.1769 | -1.0760 | NORMAL |
| PH3LIFE00004 | PH3SHADOW00004 | WS004 | 2026.05.22 11:50:00 | NO_EXPOSURE_DUPLICATE_IGNORED | NO_EXPOSURE_REVIEW_ONLY | observer_duplicate | 0 | 0.0000 | -1.0760 | NORMAL |
| PH3LIFE00005 | PH3SHADOW00005 | WS005 | 2026.05.22 12:45:00 | BLOCKED_SUSPEND_FAMILY | NO_EXPOSURE_REVIEW_ONLY | net_expectancy_below_minimum_after_proxy_cost | 0 | 0.0000 | -1.0760 | NORMAL |
| PH3LIFE00006 | PH3SHADOW00006 | WS006 | 2026.05.22 12:45:00 | NO_EXPOSURE_DUPLICATE_IGNORED | NO_EXPOSURE_REVIEW_ONLY | observer_duplicate | 0 | 0.0000 | -1.0760 | NORMAL |
| PH3LIFE00007 | PH3SHADOW00007 | WS007 | 2026.05.22 12:50:00 | WOULD_PAPER_SHADOW_OPEN | OPENED_THEN_CLOSED | synthetic_break_even | 6 | -0.2633 | -1.3393 | NORMAL |
| PH3LIFE00008 | PH3SHADOW00008 | WS008 | 2026.05.22 12:50:00 | NO_EXPOSURE_DUPLICATE_IGNORED | NO_EXPOSURE_REVIEW_ONLY | observer_duplicate | 0 | 0.0000 | -1.3393 | NORMAL |
| PH3LIFE00009 | PH3SHADOW00009 | WS009 | 2026.05.22 14:05:00 | WOULD_PAPER_SHADOW_OPEN | OPENED_THEN_CLOSED | synthetic_time_stop_small_loss | 12 | -0.4363 | -1.7756 | NORMAL |
| PH3LIFE00010 | PH3SHADOW00010 | WS010 | 2026.05.22 14:05:00 | NO_EXPOSURE_DUPLICATE_IGNORED | NO_EXPOSURE_REVIEW_ONLY | observer_duplicate | 0 | 0.0000 | -1.7756 | NORMAL |
| PH3LIFE00011 | PH3SHADOW00011 | WS011 | 2026.05.25 05:50:00 | WOULD_PAPER_SHADOW_OPEN | OPENED_THEN_CLOSED | synthetic_stop_hit | 5 | -1.1838 | -2.9594 | NORMAL |
| PH3LIFE00012 | PH3SHADOW00012 | WS012 | 2026.05.25 05:50:00 | NO_EXPOSURE_DUPLICATE_IGNORED | NO_EXPOSURE_REVIEW_ONLY | observer_duplicate | 0 | 0.0000 | -2.9594 | NORMAL |
