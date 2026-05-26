# Phase 1 Soak Drift Report

Overall status: WARN

Files directory: `C:\MT5PortableGoldMission\MQL5\Files`

## Checks

| Check | Status | Message |
| --- | --- | --- |
| decision_rows | PASS | Rows available for soak analysis: 578. |
| dry_run_state | PASS | All rows stayed in dry-run state. |
| permission_state | PASS | All rows kept permission false. |
| lifecycle_rows | PASS | Startup rows: 9; shutdown rows: 14. |
| per_run_bar_cadence | WARN | phase1-dry-run-v0.6: 2 gap(s) |
| latest_row_freshness | WARN | Latest row age is 26.7 minute(s); limit 15. |
| server_time_status | PASS | Latest row reports CLOCK_OK; historical non-CLOCK_OK rows: 1. |
| breakout_retest_observer | PASS | Observed stage values: WAIT_CONFIRMATION, WAIT_LEVEL_BREAK_RETEST, WOULD_SIGNAL |

## Runtime Summary

- Decision rows: 578
- Startup rows: 9
- Shutdown rows: 14
- Unique run IDs: 5
- First bar time: 2026.05.22 11:00:00
- Latest bar time: 2026.05.26 20:55:00
- Latest local timestamp: 2026.05.27 02:24:58
- Observer transitions: 305

## Latest Row

| Run ID | Broker Time | Bar Time | Risk | Execution | Server Time | BR Stage | BR Direction | Would Signal |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| phase1-dry-run-v0.6 | 2026.05.26 20:55:00 | 2026.05.26 20:55:00 | NORMAL | EXECUTION_OK | CLOCK_OK | WAIT_LEVEL_BREAK_RETEST | LONG | false |

## Spread Points

| count | min | median | p95 | max |
| --- | --- | --- | --- | --- |
| 578 | 50.00 | 50.00 | 75.00 | 180.00 |

## Stale Seconds

| count | min | median | p95 | max |
| --- | --- | --- | --- | --- |
| 578 | 0.00 | 0.00 | 1.00 | 55165.00 |

## State Counts

### Risk

| Value | Count |
| --- | --- |
| LOCKED_DAILY_LOSS | 1 |
| LOCKED_MONTHLY_LOSS | 1 |
| LOCKED_WEEKLY_LOSS | 1 |
| MANUAL_LOCK | 1 |
| NORMAL | 574 |

### Execution

| Value | Count |
| --- | --- |
| EXECUTION_OK | 573 |
| SPREAD_TOO_HIGH | 3 |
| STALE_TICK | 2 |

### Server Time

| Value | Count |
| --- | --- |
| CLOCK_OK | 577 |
| LOCAL_CLOCK_DRIFT | 1 |

### Breakout-Retest Stage

| Value | Count |
| --- | --- |
| WAIT_CONFIRMATION | 1 |
| WAIT_LEVEL_BREAK_RETEST | 546 |
| WOULD_SIGNAL | 31 |

### Breakout-Retest Direction

| Value | Count |
| --- | --- |
| LONG | 286 |
| NONE | 1 |
| SHORT | 291 |

### Breakout-Retest Would-Signal

| Value | Count |
| --- | --- |
| false | 547 |
| true | 31 |

## Rows By Run ID

| Run ID | Rows | First Bar | Latest Bar |
| --- | --- | --- | --- |
| phase1-dry-run-v0.6 | 574 | 2026.05.22 11:00:00 | 2026.05.26 20:55:00 |
| phase1-dry-run-v0.6-daily-lock-test | 1 | 2026.05.22 12:40:00 | 2026.05.22 12:40:00 |
| phase1-dry-run-v0.6-manual-lock-test | 1 | 2026.05.22 12:40:00 | 2026.05.22 12:40:00 |
| phase1-dry-run-v0.6-monthly-lock-test | 1 | 2026.05.22 12:40:00 | 2026.05.22 12:40:00 |
| phase1-dry-run-v0.6-weekly-lock-test | 1 | 2026.05.22 12:40:00 | 2026.05.22 12:40:00 |
