# Phase 1 Dry-Run Log Report

Overall status: WARN

Files directory: `C:\MT5PortableGoldMission\MQL5\Files`

## Checks

| Check | Status | Message |
| --- | --- | --- |
| decision_log_exists | PASS | Found C:\MT5PortableGoldMission\MQL5\Files\decision_log.csv. |
| startup_log_exists | PASS | Found C:\MT5PortableGoldMission\MQL5\Files\startup_log.csv. |
| shutdown_log_exists | PASS | Found C:\MT5PortableGoldMission\MQL5\Files\shutdown_log.csv. |
| decision_schema | PASS | Required columns present (52 checked). |
| startup_schema | PASS | Required columns present (8 checked). |
| shutdown_schema | PASS | Required columns present (9 checked). |
| decision_duplicate_headers | PASS | No duplicate CSV headers found. |
| startup_duplicate_headers | PASS | No duplicate CSV headers found. |
| shutdown_duplicate_headers | PASS | No duplicate CSV headers found. |
| decision_rows | PASS | Decision rows: 4. |
| dry_run_locked | PASS | All decision rows are dry-run. |
| trade_permission_locked | PASS | All decision rows keep permission false. |
| breakout_observation | PASS | breakout_retest appears as dry-run observed expert. |
| breakout_retest_observer | PASS | Observer stages found: WAIT_LEVEL_BREAK_RETEST |
| swing_breakout_observation | PASS | swing_breakout_retest_v0 appears as dry-run observed expert. |
| swing_breakout_retest_observer | PASS | Swing observer stages found: WAIT_LEVEL_BREAK_RETEST |
| startup_restarts | PASS | Startup rows: 2; restart append observed. |
| shutdown_rows | PASS | Shutdown rows: 13. |
| bar_cadence | PASS | Decision rows follow M5 cadence; restart duplicates are tolerated. |
| risk_state_coverage | WARN | Missing simulated state(s): LOCKED_DAILY_LOSS, LOCKED_MONTHLY_LOSS, LOCKED_WEEKLY_LOSS, MANUAL_LOCK |

## Summary

- Decision rows: 4
- Unique run IDs: 1
- Latest run ID: phase1-dry-run-v0.6

## Risk States

| Value | Count |
| --- | --- |
| NORMAL | 4 |

## Block Reasons

| Value | Count |
| --- | --- |
| phase1_dry_run_only | 4 |

## Breakout-Retest Observer

### Stages

| Value | Count |
| --- | --- |
| WAIT_LEVEL_BREAK_RETEST | 4 |

### Directions

| Value | Count |
| --- | --- |
| LONG | 3 |
| SHORT | 1 |

### Would-Signal

| Value | Count |
| --- | --- |
| false | 4 |

## Swing Breakout-Retest Observer

### Stages

| Value | Count |
| --- | --- |
| WAIT_LEVEL_BREAK_RETEST | 4 |

### Directions

| Value | Count |
| --- | --- |
| LONG | 3 |
| SHORT | 1 |

### Would-Signal

| Value | Count |
| --- | --- |
| false | 4 |

### Latest Observer Row

| Run ID | Bar Time | Stage | Direction | Reason | Level | Would Signal |
| --- | --- | --- | --- | --- | --- | --- |
| phase1-dry-run-v0.6 | 2026.05.22 11:10:00 | WAIT_LEVEL_BREAK_RETEST | SHORT | no_short_breakout_retest_candidate | 0.00 | false |
