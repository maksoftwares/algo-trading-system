# Phase 1 Soak Drift Report

Overall status: PASS

Files directory: `C:\MT5PortableGoldMission\MQL5\Files`

## Checks

| Check | Status | Message |
| --- | --- | --- |
| decision_rows | PASS | Rows available for soak analysis: 4. |
| dry_run_state | PASS | All rows stayed in dry-run state. |
| permission_state | PASS | All rows kept permission false. |
| lifecycle_rows | PASS | Startup rows: 2; shutdown rows: 13. |
| per_run_bar_cadence | PASS | No larger-than-M5 gaps inside individual run IDs. |
| latest_row_freshness | PASS | Latest row age is 0.3 minute(s); limit 15. |
| server_time_status | PASS | All rows report CLOCK_OK. |
| breakout_retest_observer | PASS | Observed stage values: WAIT_LEVEL_BREAK_RETEST |

## Runtime Summary

- Decision rows: 4
- Startup rows: 2
- Shutdown rows: 13
- Unique run IDs: 1
- First bar time: 2026.05.22 11:00:00
- Latest bar time: 2026.05.22 11:10:00
- Latest local timestamp: 2026.05.22 15:09:57
- Observer transitions: 1

## Latest Row

| Run ID | Broker Time | Bar Time | Risk | Execution | Server Time | BR Stage | BR Direction | Would Signal |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| phase1-dry-run-v0.6 | 2026.05.22 11:10:00 | 2026.05.22 11:10:00 | NORMAL | EXECUTION_OK | CLOCK_OK | WAIT_LEVEL_BREAK_RETEST | SHORT | false |

## Spread Points

| count | min | median | p95 | max |
| --- | --- | --- | --- | --- |
| 4 | 50.00 | 50.00 | 50.00 | 50.00 |

## Stale Seconds

| count | min | median | p95 | max |
| --- | --- | --- | --- | --- |
| 4 | 0.00 | 0.00 | 0.00 | 0.00 |

## State Counts

### Risk

| Value | Count |
| --- | --- |
| NORMAL | 4 |

### Execution

| Value | Count |
| --- | --- |
| EXECUTION_OK | 4 |

### Server Time

| Value | Count |
| --- | --- |
| CLOCK_OK | 4 |

### Breakout-Retest Stage

| Value | Count |
| --- | --- |
| WAIT_LEVEL_BREAK_RETEST | 4 |

### Breakout-Retest Direction

| Value | Count |
| --- | --- |
| LONG | 3 |
| SHORT | 1 |

### Breakout-Retest Would-Signal

| Value | Count |
| --- | --- |
| false | 4 |

## Rows By Run ID

| Run ID | Rows | First Bar | Latest Bar |
| --- | --- | --- | --- |
| phase1-dry-run-v0.6 | 4 | 2026.05.22 11:00:00 | 2026.05.22 11:10:00 |
