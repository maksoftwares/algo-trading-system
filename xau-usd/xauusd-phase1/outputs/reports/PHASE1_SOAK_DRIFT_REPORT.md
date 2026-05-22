# Phase 1 Soak Drift Report

Overall status: PASS

Files directory: `C:\MT5PortableGoldMission\MQL5\Files`

## Checks

| Check | Status | Message |
| --- | --- | --- |
| decision_rows | PASS | Rows available for soak analysis: 27. |
| dry_run_state | PASS | All rows stayed in dry-run state. |
| permission_state | PASS | All rows kept permission false. |
| lifecycle_rows | PASS | Startup rows: 7; shutdown rows: 13. |
| per_run_bar_cadence | PASS | No larger-than-M5 gaps inside individual run IDs. |
| latest_row_freshness | PASS | Latest row age is 0.3 minute(s); limit 15. |
| server_time_status | PASS | All rows report CLOCK_OK. |
| breakout_retest_observer | PASS | Observed stage values: WAIT_LEVEL_BREAK_RETEST, WOULD_SIGNAL |

## Runtime Summary

- Decision rows: 27
- Startup rows: 7
- Shutdown rows: 13
- Unique run IDs: 5
- First bar time: 2026.05.22 11:00:00
- Latest bar time: 2026.05.22 12:40:00
- Latest local timestamp: 2026.05.22 16:42:03
- Observer transitions: 11

## Latest Row

| Run ID | Broker Time | Bar Time | Risk | Execution | Server Time | BR Stage | BR Direction | Would Signal |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| phase1-dry-run-v0.6 | 2026.05.22 12:42:07 | 2026.05.22 12:40:00 | NORMAL | EXECUTION_OK | CLOCK_OK | WAIT_LEVEL_BREAK_RETEST | SHORT | false |

## Spread Points

| count | min | median | p95 | max |
| --- | --- | --- | --- | --- |
| 27 | 50.00 | 50.00 | 75.00 | 75.00 |

## Stale Seconds

| count | min | median | p95 | max |
| --- | --- | --- | --- | --- |
| 27 | 0.00 | 0.00 | 1.00 | 1.00 |

## State Counts

### Risk

| Value | Count |
| --- | --- |
| LOCKED_DAILY_LOSS | 1 |
| LOCKED_MONTHLY_LOSS | 1 |
| LOCKED_WEEKLY_LOSS | 1 |
| MANUAL_LOCK | 1 |
| NORMAL | 23 |

### Execution

| Value | Count |
| --- | --- |
| EXECUTION_OK | 27 |

### Server Time

| Value | Count |
| --- | --- |
| CLOCK_OK | 27 |

### Breakout-Retest Stage

| Value | Count |
| --- | --- |
| WAIT_LEVEL_BREAK_RETEST | 25 |
| WOULD_SIGNAL | 2 |

### Breakout-Retest Direction

| Value | Count |
| --- | --- |
| LONG | 11 |
| SHORT | 16 |

### Breakout-Retest Would-Signal

| Value | Count |
| --- | --- |
| false | 25 |
| true | 2 |

## Rows By Run ID

| Run ID | Rows | First Bar | Latest Bar |
| --- | --- | --- | --- |
| phase1-dry-run-v0.6 | 23 | 2026.05.22 11:00:00 | 2026.05.22 12:40:00 |
| phase1-dry-run-v0.6-daily-lock-test | 1 | 2026.05.22 12:40:00 | 2026.05.22 12:40:00 |
| phase1-dry-run-v0.6-manual-lock-test | 1 | 2026.05.22 12:40:00 | 2026.05.22 12:40:00 |
| phase1-dry-run-v0.6-monthly-lock-test | 1 | 2026.05.22 12:40:00 | 2026.05.22 12:40:00 |
| phase1-dry-run-v0.6-weekly-lock-test | 1 | 2026.05.22 12:40:00 | 2026.05.22 12:40:00 |
