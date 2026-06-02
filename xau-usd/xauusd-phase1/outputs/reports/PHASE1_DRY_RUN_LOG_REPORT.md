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
| decision_rows | PASS | Decision rows: 1819. |
| dry_run_locked | PASS | All decision rows are dry-run. |
| trade_permission_locked | PASS | All decision rows keep permission false. |
| breakout_observation | PASS | breakout_retest appears as dry-run observed expert. |
| breakout_retest_observer | PASS | Observer stages found: WAIT_CONFIRMATION, WAIT_LEVEL_BREAK_RETEST, WOULD_SIGNAL |
| swing_breakout_observation | PASS | swing_breakout_retest_v0 appears as dry-run observed expert. |
| swing_breakout_retest_observer | PASS | Swing observer stages found: WAIT_CONFIRMATION, WAIT_LEVEL_BREAK_RETEST, WOULD_SIGNAL |
| startup_restarts | PASS | Startup rows: 5; restart append observed. |
| shutdown_rows | PASS | Shutdown rows: 16. |
| bar_cadence | PASS | Decision rows follow M5 cadence outside expected market breaks; tolerated gaps: 9. |
| risk_state_coverage | PASS | All simulated lock states observed. |

## Summary

- Decision rows: 1819
- Unique run IDs: 6
- Latest run ID: phase1-dry-run-v0.7
- Current run rows: 1086

## Risk States

| Value | Count |
| --- | --- |
| LOCKED_DAILY_LOSS | 1 |
| LOCKED_MONTHLY_LOSS | 1 |
| LOCKED_WEEKLY_LOSS | 1 |
| MANUAL_LOCK | 1 |
| NORMAL | 1815 |

## Block Reasons

| Value | Count |
| --- | --- |
| COST_REVALIDATION_PENDING | 73 |
| COST_SUSPENDED | 7 |
| LOCAL_CLOCK_DRIFT | 3 |
| LOCKED_DAILY_LOSS | 1 |
| LOCKED_MONTHLY_LOSS | 1 |
| LOCKED_WEEKLY_LOSS | 1 |
| MANUAL_LOCK | 1 |
| SPREAD_TOO_HIGH | 9 |
| STALE_TICK | 1 |
| phase1_dry_run_only | 1722 |

## Current Run Block Reasons

Only the latest run_id determines the current lifecycle interpretation. Older run IDs remain audit history.

| Value | Count |
| --- | --- |
| COST_REVALIDATION_PENDING | 73 |
| LOCAL_CLOCK_DRIFT | 2 |
| SPREAD_TOO_HIGH | 3 |
| phase1_dry_run_only | 1008 |

## Breakout-Retest Observer

### Stages

| Value | Count |
| --- | --- |
| WAIT_CONFIRMATION | 3 |
| WAIT_LEVEL_BREAK_RETEST | 1703 |
| WOULD_SIGNAL | 113 |

### Directions

| Value | Count |
| --- | --- |
| LONG | 906 |
| NONE | 3 |
| SHORT | 910 |

### Would-Signal

| Value | Count |
| --- | --- |
| false | 1706 |
| true | 113 |

## Swing Breakout-Retest Observer

### Stages

| Value | Count |
| --- | --- |
| WAIT_CONFIRMATION | 3 |
| WAIT_LEVEL_BREAK_RETEST | 1728 |
| WOULD_SIGNAL | 88 |

### Directions

| Value | Count |
| --- | --- |
| LONG | 906 |
| NONE | 3 |
| SHORT | 910 |

### Would-Signal

| Value | Count |
| --- | --- |
| false | 1731 |
| true | 88 |

### Latest Observer Row

| Run ID | Bar Time | Stage | Direction | Reason | Level | Would Signal |
| --- | --- | --- | --- | --- | --- | --- |
| phase1-dry-run-v0.7 | 2026.06.02 10:20:00 | WAIT_LEVEL_BREAK_RETEST | LONG | no_long_breakout_retest_candidate | 0.00 | false |
