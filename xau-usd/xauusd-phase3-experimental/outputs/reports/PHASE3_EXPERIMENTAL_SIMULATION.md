# Phase 3 Experimental Offline Simulation

Overall status: EXPERIMENTAL_ACTIVE

## Boundary

- This is a repo-only experiment.
- Real Phase 2 readiness remains unchanged.
- The live MT5 dry-run and passive spread logger are not modified.
- No broker-action path is implemented or authorized.

## Summary

| Metric | Value |
| --- | --- |
| Accepted events | 87 |
| Rejected source rows | 2 |
| Baseline net expectancy R | 0.1888 |
| Median proxy cost R | 0.1277 |
| Median net after proxy cost R | 0.3839 |
| Minimum net expectancy R | 0.15 |

## Kill Rule Counts

| Metric | Value |
| --- | --- |
| NORMAL | 87 |

## Sample Events

| event_id | observer | decision_bar_time | direction | measured_cost_r_proxy | net_expectancy_r_after_proxy_cost | kill_rule_state |
| --- | --- | --- | --- | --- | --- | --- |
| PH3EXP00001 | breakout_retest | 2026.05.22 11:25:00 | SHORT | 0.1265 | 0.3851 | NORMAL |
| PH3EXP00002 | swing_breakout_retest_v0 | 2026.05.22 11:25:00 | SHORT | 0.1265 | 0.3851 | NORMAL |
| PH3EXP00003 | breakout_retest | 2026.05.22 11:50:00 | LONG | 0.0865 | 0.4251 | NORMAL |
| PH3EXP00004 | swing_breakout_retest_v0 | 2026.05.22 11:50:00 | LONG | 0.0865 | 0.4251 | NORMAL |
| PH3EXP00005 | breakout_retest | 2026.05.22 12:45:00 | LONG | 0.1867 | 0.3249 | NORMAL |
| PH3EXP00006 | swing_breakout_retest_v0 | 2026.05.22 12:45:00 | LONG | 0.1867 | 0.3249 | NORMAL |
| PH3EXP00007 | breakout_retest | 2026.05.22 12:50:00 | LONG | 0.1316 | 0.3800 | NORMAL |
| PH3EXP00008 | swing_breakout_retest_v0 | 2026.05.22 12:50:00 | LONG | 0.1316 | 0.3800 | NORMAL |
| PH3EXP00009 | breakout_retest | 2026.05.22 14:05:00 | SHORT | 0.0931 | 0.4185 | NORMAL |
| PH3EXP00010 | swing_breakout_retest_v0 | 2026.05.22 14:05:00 | SHORT | 0.0931 | 0.4185 | NORMAL |
