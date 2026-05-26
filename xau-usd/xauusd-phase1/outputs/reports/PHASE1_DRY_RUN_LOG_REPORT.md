# Phase 1 Dry-Run Log Report

Overall status: FAIL

Files directory: `C:\MT5PortableGoldMission\MQL5\Files`

## Checks

| Check | Status | Message |
| --- | --- | --- |
| decision_log_exists | PASS | Found C:\MT5PortableGoldMission\MQL5\Files\decision_log.csv. |
| startup_log_exists | PASS | Found C:\MT5PortableGoldMission\MQL5\Files\startup_log.csv. |
| shutdown_log_exists | PASS | Found C:\MT5PortableGoldMission\MQL5\Files\shutdown_log.csv. |
| decision_schema | FAIL | Missing column(s): decision_schema_version, decision_schema_hash, br_lifecycle_state, sbr_lifecycle_state |
| decision_schema_hash | FAIL | schema_version=missing; expected_schema_hash=ee45252876eff387cd75ddbd350230b15872b18316f0508a24a4a19dcc657e60; observed_schema_hash=36a3551d241f7a68df88bd7edd504a5a90a2252f353782654b39fbf5f71d3803. |
| startup_schema | FAIL | Missing column(s): decision_schema_version, decision_schema_hash, decision_schema_rotation_performed, decision_schema_rotation_reason, decision_schema_archive_path |
| decision_schema_rotation | FAIL | Startup schema hash is missing; expected_schema_hash=ee45252876eff387cd75ddbd350230b15872b18316f0508a24a4a19dcc657e60. |
| shutdown_schema | PASS | Required columns present (9 checked). |
| decision_duplicate_headers | PASS | No duplicate CSV headers found. |
| startup_duplicate_headers | PASS | No duplicate CSV headers found. |
| shutdown_duplicate_headers | PASS | No duplicate CSV headers found. |
| decision_rows | PASS | Decision rows: 596. |
| dry_run_locked | PASS | All decision rows are dry-run. |
| trade_permission_locked | PASS | All decision rows keep permission false. |
| breakout_observation | PASS | breakout_retest appears as dry-run observed expert. |
| breakout_retest_observer | PASS | Observer stages found: WAIT_CONFIRMATION, WAIT_LEVEL_BREAK_RETEST, WOULD_SIGNAL |
| swing_breakout_observation | PASS | swing_breakout_retest_v0 appears as dry-run observed expert. |
| swing_breakout_retest_observer | PASS | Swing observer stages found: WAIT_CONFIRMATION, WAIT_LEVEL_BREAK_RETEST, WOULD_SIGNAL |
| startup_restarts | PASS | Startup rows: 9; restart append observed. |
| shutdown_rows | PASS | Shutdown rows: 14. |
| bar_cadence | WARN | Larger-than-M5 gaps found: 1. |
| risk_state_coverage | PASS | All simulated lock states observed. |

## Summary

- Decision rows: 596
- Unique run IDs: 5
- Latest run ID: phase1-dry-run-v0.6

## Risk States

| Value | Count |
| --- | --- |
| LOCKED_DAILY_LOSS | 1 |
| LOCKED_MONTHLY_LOSS | 1 |
| LOCKED_WEEKLY_LOSS | 1 |
| MANUAL_LOCK | 1 |
| NORMAL | 592 |

## Block Reasons

| Value | Count |
| --- | --- |
| LOCAL_CLOCK_DRIFT | 1 |
| LOCKED_DAILY_LOSS | 1 |
| LOCKED_MONTHLY_LOSS | 1 |
| LOCKED_WEEKLY_LOSS | 1 |
| MANUAL_LOCK | 1 |
| SPREAD_TOO_HIGH | 6 |
| STALE_TICK | 1 |
| phase1_dry_run_only | 584 |

## Breakout-Retest Observer

### Stages

| Value | Count |
| --- | --- |
| WAIT_CONFIRMATION | 1 |
| WAIT_LEVEL_BREAK_RETEST | 562 |
| WOULD_SIGNAL | 33 |

### Directions

| Value | Count |
| --- | --- |
| LONG | 295 |
| NONE | 1 |
| SHORT | 300 |

### Would-Signal

| Value | Count |
| --- | --- |
| false | 563 |
| true | 33 |

## Swing Breakout-Retest Observer

### Stages

| Value | Count |
| --- | --- |
| WAIT_CONFIRMATION | 1 |
| WAIT_LEVEL_BREAK_RETEST | 563 |
| WOULD_SIGNAL | 32 |

### Directions

| Value | Count |
| --- | --- |
| LONG | 295 |
| NONE | 1 |
| SHORT | 300 |

### Would-Signal

| Value | Count |
| --- | --- |
| false | 564 |
| true | 32 |

### Latest Observer Row

| Run ID | Bar Time | Stage | Direction | Reason | Level | Would Signal |
| --- | --- | --- | --- | --- | --- | --- |
| phase1-dry-run-v0.6 | 2026.05.26 23:25:00 | WAIT_LEVEL_BREAK_RETEST | SHORT | no_short_breakout_retest_candidate | 0.00 | false |
