# Phase 1 Dry-Run Log Report

Overall status: PASS

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
| decision_rows | PASS | Decision rows: 27. |
| dry_run_locked | PASS | All decision rows are dry-run. |
| trade_permission_locked | PASS | All decision rows keep permission false. |
| breakout_observation | PASS | breakout_retest appears as dry-run observed expert. |
| breakout_retest_observer | PASS | Observer stages found: WAIT_LEVEL_BREAK_RETEST, WOULD_SIGNAL |
| swing_breakout_observation | PASS | swing_breakout_retest_v0 appears as dry-run observed expert. |
| swing_breakout_retest_observer | PASS | Swing observer stages found: WAIT_LEVEL_BREAK_RETEST, WOULD_SIGNAL |
| startup_restarts | PASS | Startup rows: 7; restart append observed. |
| shutdown_rows | PASS | Shutdown rows: 13. |
| bar_cadence | PASS | Decision rows follow M5 cadence; restart duplicates are tolerated. |
| risk_state_coverage | PASS | All simulated lock states observed. |

## Summary

- Decision rows: 27
- Unique run IDs: 5
- Latest run ID: phase1-dry-run-v0.6

## Risk States

| Value | Count |
| --- | --- |
| LOCKED_DAILY_LOSS | 1 |
| LOCKED_MONTHLY_LOSS | 1 |
| LOCKED_WEEKLY_LOSS | 1 |
| MANUAL_LOCK | 1 |
| NORMAL | 23 |

## Block Reasons

| Value | Count |
| --- | --- |
| LOCKED_DAILY_LOSS | 1 |
| LOCKED_MONTHLY_LOSS | 1 |
| LOCKED_WEEKLY_LOSS | 1 |
| MANUAL_LOCK | 1 |
| phase1_dry_run_only | 23 |

## Breakout-Retest Observer

### Stages

| Value | Count |
| --- | --- |
| WAIT_LEVEL_BREAK_RETEST | 25 |
| WOULD_SIGNAL | 2 |

### Directions

| Value | Count |
| --- | --- |
| LONG | 11 |
| SHORT | 16 |

### Would-Signal

| Value | Count |
| --- | --- |
| false | 25 |
| true | 2 |

## Swing Breakout-Retest Observer

### Stages

| Value | Count |
| --- | --- |
| WAIT_LEVEL_BREAK_RETEST | 25 |
| WOULD_SIGNAL | 2 |

### Directions

| Value | Count |
| --- | --- |
| LONG | 11 |
| SHORT | 16 |

### Would-Signal

| Value | Count |
| --- | --- |
| false | 25 |
| true | 2 |

### Latest Observer Row

| Run ID | Bar Time | Stage | Direction | Reason | Level | Would Signal |
| --- | --- | --- | --- | --- | --- | --- |
| phase1-dry-run-v0.6 | 2026.05.22 12:40:00 | WAIT_LEVEL_BREAK_RETEST | SHORT | no_short_breakout_retest_candidate | 0.00 | false |
