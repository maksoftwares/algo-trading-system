# Phase 1 Soak Drift Report

Overall status: PASS

Files directory: `C:\MT5PortableGoldMission\MQL5\Files`

## Checks

| Check | Status | Message |
| --- | --- | --- |
| decision_rows | PASS | Rows available for soak analysis: 190. |
| dry_run_state | PASS | All rows stayed in dry-run state. |
| permission_state | PASS | All rows kept permission false. |
| lifecycle_rows | PASS | Startup rows: 15; shutdown rows: 13. |
| per_run_bar_cadence | PASS | phase1-dry-run-v0.5: 1 expected market-break gap(s) |
| latest_row_freshness | PASS | Latest row age is 0.2 minute(s); limit 15. |
| server_time_status | PASS | All rows report CLOCK_OK. |
| breakout_retest_observer | PASS | Observed stage values: WAIT_LEVEL_BREAK_RETEST, WOULD_SIGNAL |

## Runtime Summary

- Decision rows: 190
- Startup rows: 15
- Shutdown rows: 13
- Unique run IDs: 5
- First bar time: 2026.05.21 13:45:00
- Latest bar time: 2026.05.22 06:05:00
- Latest local timestamp: 2026.05.22 10:04:57
- Observer transitions: 118

## Latest Row

| Run ID | Broker Time | Bar Time | Risk | Execution | Server Time | BR Stage | BR Direction | Would Signal |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| phase1-dry-run-v0.5 | 2026.05.22 06:05:00 | 2026.05.22 06:05:00 | NORMAL | EXECUTION_OK | CLOCK_OK | WAIT_LEVEL_BREAK_RETEST | LONG | false |

## Spread Points

| count | min | median | p95 | max |
| --- | --- | --- | --- | --- |
| 190 | 50.00 | 50.00 | 75.00 | 95.00 |

## Stale Seconds

| count | min | median | p95 | max |
| --- | --- | --- | --- | --- |
| 190 | 0.00 | 0.00 | 0.00 | 1.00 |

## State Counts

### Risk

| Value | Count |
| --- | --- |
| LOCKED_DAILY_LOSS | 1 |
| LOCKED_MONTHLY_LOSS | 1 |
| LOCKED_WEEKLY_LOSS | 1 |
| MANUAL_LOCK | 1 |
| NORMAL | 186 |

### Execution

| Value | Count |
| --- | --- |
| EXECUTION_OK | 189 |
| SPREAD_TOO_HIGH | 1 |

### Server Time

| Value | Count |
| --- | --- |
| CLOCK_OK | 190 |

### Breakout-Retest Stage

| Value | Count |
| --- | --- |
| WAIT_LEVEL_BREAK_RETEST | 177 |
| WOULD_SIGNAL | 13 |

### Breakout-Retest Direction

| Value | Count |
| --- | --- |
| LONG | 102 |
| SHORT | 88 |

### Breakout-Retest Would-Signal

| Value | Count |
| --- | --- |
| false | 177 |
| true | 13 |

## Rows By Run ID

| Run ID | Rows | First Bar | Latest Bar |
| --- | --- | --- | --- |
| phase1-dry-run-v0.5 | 186 | 2026.05.21 13:45:00 | 2026.05.22 06:05:00 |
| phase1-dry-run-v0.5-daily-lock-test | 1 | 2026.05.21 13:50:00 | 2026.05.21 13:50:00 |
| phase1-dry-run-v0.5-manual-lock-test | 1 | 2026.05.21 13:50:00 | 2026.05.21 13:50:00 |
| phase1-dry-run-v0.5-monthly-lock-test | 1 | 2026.05.21 13:50:00 | 2026.05.21 13:50:00 |
| phase1-dry-run-v0.5-weekly-lock-test | 1 | 2026.05.21 13:50:00 | 2026.05.21 13:50:00 |
