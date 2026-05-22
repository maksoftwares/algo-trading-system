# Phase 1 Soak Drift Report

Overall status: PASS

Files directory: `C:\MT5PortableGoldMission\MQL5\Files`

## Checks

| Check | Status | Message |
| --- | --- | --- |
| decision_rows | PASS | Rows available for soak analysis: 213. |
| dry_run_state | PASS | All rows stayed in dry-run state. |
| permission_state | PASS | All rows kept permission false. |
| lifecycle_rows | PASS | Startup rows: 15; shutdown rows: 13. |
| per_run_bar_cadence | PASS | phase1-dry-run-v0.5: 1 expected market-break gap(s) |
| latest_row_freshness | PASS | Latest row age is 1.2 minute(s); limit 15. |
| server_time_status | PASS | All rows report CLOCK_OK. |
| breakout_retest_observer | PASS | Observed stage values: WAIT_LEVEL_BREAK_RETEST, WOULD_SIGNAL |

## Runtime Summary

- Decision rows: 213
- Startup rows: 15
- Shutdown rows: 13
- Unique run IDs: 5
- First bar time: 2026.05.21 13:45:00
- Latest bar time: 2026.05.22 08:00:00
- Latest local timestamp: 2026.05.22 11:59:57
- Observer transitions: 131

## Latest Row

| Run ID | Broker Time | Bar Time | Risk | Execution | Server Time | BR Stage | BR Direction | Would Signal |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| phase1-dry-run-v0.5 | 2026.05.22 08:00:00 | 2026.05.22 08:00:00 | NORMAL | EXECUTION_OK | CLOCK_OK | WAIT_LEVEL_BREAK_RETEST | LONG | false |

## Spread Points

| count | min | median | p95 | max |
| --- | --- | --- | --- | --- |
| 213 | 50.00 | 50.00 | 75.00 | 95.00 |

## Stale Seconds

| count | min | median | p95 | max |
| --- | --- | --- | --- | --- |
| 213 | 0.00 | 0.00 | 0.00 | 1.00 |

## State Counts

### Risk

| Value | Count |
| --- | --- |
| LOCKED_DAILY_LOSS | 1 |
| LOCKED_MONTHLY_LOSS | 1 |
| LOCKED_WEEKLY_LOSS | 1 |
| MANUAL_LOCK | 1 |
| NORMAL | 209 |

### Execution

| Value | Count |
| --- | --- |
| EXECUTION_OK | 212 |
| SPREAD_TOO_HIGH | 1 |

### Server Time

| Value | Count |
| --- | --- |
| CLOCK_OK | 213 |

### Breakout-Retest Stage

| Value | Count |
| --- | --- |
| WAIT_LEVEL_BREAK_RETEST | 199 |
| WOULD_SIGNAL | 14 |

### Breakout-Retest Direction

| Value | Count |
| --- | --- |
| LONG | 114 |
| SHORT | 99 |

### Breakout-Retest Would-Signal

| Value | Count |
| --- | --- |
| false | 199 |
| true | 14 |

## Rows By Run ID

| Run ID | Rows | First Bar | Latest Bar |
| --- | --- | --- | --- |
| phase1-dry-run-v0.5 | 209 | 2026.05.21 13:45:00 | 2026.05.22 08:00:00 |
| phase1-dry-run-v0.5-daily-lock-test | 1 | 2026.05.21 13:50:00 | 2026.05.21 13:50:00 |
| phase1-dry-run-v0.5-manual-lock-test | 1 | 2026.05.21 13:50:00 | 2026.05.21 13:50:00 |
| phase1-dry-run-v0.5-monthly-lock-test | 1 | 2026.05.21 13:50:00 | 2026.05.21 13:50:00 |
| phase1-dry-run-v0.5-weekly-lock-test | 1 | 2026.05.21 13:50:00 | 2026.05.21 13:50:00 |
