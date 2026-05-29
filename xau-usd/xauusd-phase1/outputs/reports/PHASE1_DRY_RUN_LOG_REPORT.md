# Phase 1 Dry-Run Log Report

Overall status: PASS

Files directory: `C:\MT5PortableGoldMission\MQL5\Files`

## Checks

| Check | Status | Message |
| --- | --- | --- |
| decision_log_exists | PASS | Found C:\MT5PortableGoldMission\MQL5\Files\decision_log.csv. |
| startup_log_exists | PASS | Found C:\MT5PortableGoldMission\MQL5\Files\startup_log.csv. |
| shutdown_log_exists | PASS | Found C:\MT5PortableGoldMission\MQL5\Files\shutdown_log.csv. |
| decision_schema | PASS | Required columns present (56 checked). |
| decision_schema_hash | PASS | schema_version=phase1_decision_schema_v2; expected_schema_hash=ee45252876eff387cd75ddbd350230b15872b18316f0508a24a4a19dcc657e60; observed_schema_hash=ee45252876eff387cd75ddbd350230b15872b18316f0508a24a4a19dcc657e60. |
| startup_schema | PASS | Required columns present (13 checked). |
| decision_schema_rotation | PASS | rotation_performed=false; current schema already matched. |
| shutdown_schema | PASS | Required columns present (9 checked). |
| decision_duplicate_headers | PASS | No duplicate CSV headers found. |
| startup_duplicate_headers | PASS | No duplicate CSV headers found. |
| shutdown_duplicate_headers | PASS | No duplicate CSV headers found. |
| decision_rows | PASS | Decision rows: 1297. |
| dry_run_locked | PASS | All decision rows are dry-run. |
| trade_permission_locked | PASS | All decision rows keep permission false. |
| breakout_observation | PASS | breakout_retest appears as dry-run observed expert. |
| breakout_retest_observer | PASS | Observer stages found: WAIT_CONFIRMATION, WAIT_LEVEL_BREAK_RETEST, WOULD_SIGNAL |
| swing_breakout_observation | PASS | swing_breakout_retest_v0 appears as dry-run observed expert. |
| swing_breakout_retest_observer | PASS | Swing observer stages found: WAIT_CONFIRMATION, WAIT_LEVEL_BREAK_RETEST, WOULD_SIGNAL |
| startup_restarts | PASS | Startup rows: 3; restart append observed. |
| shutdown_rows | PASS | Shutdown rows: 14. |
| bar_cadence | PASS | Decision rows follow M5 cadence outside expected market breaks; tolerated gaps: 6. |
| risk_state_coverage | PASS | All simulated lock states observed. |

## Summary

- Decision rows: 1297
- Unique run IDs: 6
- Latest run ID: phase1-dry-run-v0.7
- Current run rows: 564

## Risk States

| Value | Count |
| --- | --- |
| LOCKED_DAILY_LOSS | 1 |
| LOCKED_MONTHLY_LOSS | 1 |
| LOCKED_WEEKLY_LOSS | 1 |
| MANUAL_LOCK | 1 |
| NORMAL | 1293 |

## Block Reasons

| Value | Count |
| --- | --- |
| COST_REVALIDATION_PENDING | 43 |
| COST_SUSPENDED | 7 |
| LOCAL_CLOCK_DRIFT | 1 |
| LOCKED_DAILY_LOSS | 1 |
| LOCKED_MONTHLY_LOSS | 1 |
| LOCKED_WEEKLY_LOSS | 1 |
| MANUAL_LOCK | 1 |
| SPREAD_TOO_HIGH | 8 |
| STALE_TICK | 1 |
| phase1_dry_run_only | 1233 |

## Current Run Block Reasons

Only the latest run_id determines the current lifecycle interpretation. Older run IDs remain audit history.

| Value | Count |
| --- | --- |
| COST_REVALIDATION_PENDING | 43 |
| SPREAD_TOO_HIGH | 2 |
| phase1_dry_run_only | 519 |

## Breakout-Retest Observer

### Stages

| Value | Count |
| --- | --- |
| WAIT_CONFIRMATION | 3 |
| WAIT_LEVEL_BREAK_RETEST | 1211 |
| WOULD_SIGNAL | 83 |

### Directions

| Value | Count |
| --- | --- |
| LONG | 652 |
| NONE | 3 |
| SHORT | 642 |

### Would-Signal

| Value | Count |
| --- | --- |
| false | 1214 |
| true | 83 |

## Swing Breakout-Retest Observer

### Stages

| Value | Count |
| --- | --- |
| WAIT_CONFIRMATION | 3 |
| WAIT_LEVEL_BREAK_RETEST | 1229 |
| WOULD_SIGNAL | 65 |

### Directions

| Value | Count |
| --- | --- |
| LONG | 652 |
| NONE | 3 |
| SHORT | 642 |

### Would-Signal

| Value | Count |
| --- | --- |
| false | 1232 |
| true | 65 |

### Latest Observer Row

| Run ID | Bar Time | Stage | Direction | Reason | Level | Would Signal |
| --- | --- | --- | --- | --- | --- | --- |
| phase1-dry-run-v0.7 | 2026.05.29 11:35:00 | WAIT_LEVEL_BREAK_RETEST | SHORT | no_short_breakout_retest_candidate | 0.00 | false |
