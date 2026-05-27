# Phase 3 Experimental Offline Simulation

This report has no authority over Phase 2 readiness. PHASE2_READINESS_REPORT.md remains the sole real readiness authority.

Overall status: EXPERIMENTAL_COST_SUSPEND_SCENARIO

## Boundary

- This is a repo-only experiment.
- Real Phase 2 readiness remains unchanged.
- The live MT5 dry-run and passive spread logger are not modified.
- No broker-action path is implemented or authorized.

## Summary

| Metric | Value |
| --- | --- |
| Raw observer events | 87 |
| Family unique events | 47 |
| Primary stream allowed | 47 |
| Observer duplicates | 40 |
| Observer conflicts | 0 |
| Rejected source rows | 2 |
| Cost mode | entry_exit_proxy |
| Baseline net expectancy R | 0.1888 |
| Median proxy cost R | 0.2554 |
| Median net after proxy cost R | 0.2562 |
| Minimum net expectancy R | 0.15 |

## Family Role Counts

| Metric | Value |
| --- | --- |
| OBSERVER_DUPLICATE | 40 |
| PRIMARY_EXECUTION_CANDIDATE | 47 |

## Kill Rule Counts

| Metric | Value |
| --- | --- |
| COST_WATCH | 2 |
| NORMAL | 66 |
| SUSPEND_FAMILY | 19 |

## Sample Events

| event_id | family_event_id | family_event_role | primary_stream_allowed | observer | decision_bar_time | direction | cost_mode | measured_cost_r_proxy | net_expectancy_r_after_proxy_cost | kill_rule_state |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PH3EXP00001 | FAM00001 | PRIMARY_EXECUTION_CANDIDATE | true | breakout_retest | 2026.05.22 11:25:00 | SHORT | entry_exit_proxy | 0.2529 | 0.2587 | NORMAL |
| PH3EXP00002 | FAM00001 | OBSERVER_DUPLICATE | false | swing_breakout_retest_v0 | 2026.05.22 11:25:00 | SHORT | entry_exit_proxy | 0.2529 | 0.2587 | NORMAL |
| PH3EXP00003 | FAM00002 | PRIMARY_EXECUTION_CANDIDATE | true | breakout_retest | 2026.05.22 11:50:00 | LONG | entry_exit_proxy | 0.1731 | 0.3385 | NORMAL |
| PH3EXP00004 | FAM00002 | OBSERVER_DUPLICATE | false | swing_breakout_retest_v0 | 2026.05.22 11:50:00 | LONG | entry_exit_proxy | 0.1731 | 0.3385 | NORMAL |
| PH3EXP00005 | FAM00003 | PRIMARY_EXECUTION_CANDIDATE | true | breakout_retest | 2026.05.22 12:45:00 | LONG | entry_exit_proxy | 0.3734 | 0.1382 | SUSPEND_FAMILY |
| PH3EXP00006 | FAM00003 | OBSERVER_DUPLICATE | false | swing_breakout_retest_v0 | 2026.05.22 12:45:00 | LONG | entry_exit_proxy | 0.3734 | 0.1382 | SUSPEND_FAMILY |
| PH3EXP00007 | FAM00004 | PRIMARY_EXECUTION_CANDIDATE | true | breakout_retest | 2026.05.22 12:50:00 | LONG | entry_exit_proxy | 0.2633 | 0.2483 | NORMAL |
| PH3EXP00008 | FAM00004 | OBSERVER_DUPLICATE | false | swing_breakout_retest_v0 | 2026.05.22 12:50:00 | LONG | entry_exit_proxy | 0.2633 | 0.2483 | NORMAL |
| PH3EXP00009 | FAM00005 | PRIMARY_EXECUTION_CANDIDATE | true | breakout_retest | 2026.05.22 14:05:00 | SHORT | entry_exit_proxy | 0.1863 | 0.3253 | NORMAL |
| PH3EXP00010 | FAM00005 | OBSERVER_DUPLICATE | false | swing_breakout_retest_v0 | 2026.05.22 14:05:00 | SHORT | entry_exit_proxy | 0.1863 | 0.3253 | NORMAL |
