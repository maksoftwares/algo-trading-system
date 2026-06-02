# Phase 1 Soak Drift Report

Overall status: PASS

Files directory: `C:\MT5PortableGoldMission\MQL5\Files`

## Checks

| Check | Status | Message |
| --- | --- | --- |
| decision_rows | PASS | Rows available for soak analysis: 1793. |
| dry_run_state | PASS | All rows stayed in dry-run state. |
| permission_state | PASS | All rows kept permission false. |
| lifecycle_rows | PASS | Startup rows: 5; shutdown rows: 16. |
| per_run_bar_cadence | PASS | phase1-dry-run-v0.6: 4 expected market-break gap(s); phase1-dry-run-v0.7: 5 expected market-break gap(s) |
| latest_row_freshness | PASS | Latest row age is 3.3 minute(s); limit 240. |
| server_time_status | PASS | Latest row reports CLOCK_OK; historical non-CLOCK_OK rows: 3. |
| breakout_retest_observer | PASS | Observed stage values: WAIT_CONFIRMATION, WAIT_LEVEL_BREAK_RETEST, WOULD_SIGNAL |

## Runtime Summary

- Decision rows: 1793
- Startup rows: 5
- Shutdown rows: 16
- Unique run IDs: 6
- First bar time: 2026.05.22 11:00:00
- Latest bar time: 2026.06.02 08:10:00
- Latest local timestamp: 2026.06.02 12:09:57
- Observer transitions: 977

## Latest Row

| Run ID | Broker Time | Bar Time | Risk | Execution | Server Time | BR Stage | BR Direction | Would Signal |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| phase1-dry-run-v0.7 | 2026.06.02 08:10:00 | 2026.06.02 08:10:00 | NORMAL | EXECUTION_OK | CLOCK_OK | WAIT_LEVEL_BREAK_RETEST | LONG | false |

## Spread Points

| count | min | median | p95 | max |
| --- | --- | --- | --- | --- |
| 1793 | 50.00 | 50.00 | 75.00 | 180.00 |

## Stale Seconds

| count | min | median | p95 | max |
| --- | --- | --- | --- | --- |
| 1793 | 0.00 | 0.00 | 1.00 | 55165.00 |

## State Counts

### Risk

| Value | Count |
| --- | --- |
| LOCKED_DAILY_LOSS | 1 |
| LOCKED_MONTHLY_LOSS | 1 |
| LOCKED_WEEKLY_LOSS | 1 |
| MANUAL_LOCK | 1 |
| NORMAL | 1789 |

### Execution

| Value | Count |
| --- | --- |
| EXECUTION_OK | 1782 |
| SPREAD_TOO_HIGH | 9 |
| STALE_TICK | 2 |

### Server Time

| Value | Count |
| --- | --- |
| CLOCK_OK | 1790 |
| LOCAL_CLOCK_DRIFT | 3 |

### Breakout-Retest Stage

| Value | Count |
| --- | --- |
| WAIT_CONFIRMATION | 3 |
| WAIT_LEVEL_BREAK_RETEST | 1678 |
| WOULD_SIGNAL | 112 |

### Breakout-Retest Direction

| Value | Count |
| --- | --- |
| LONG | 894 |
| NONE | 3 |
| SHORT | 896 |

### Breakout-Retest Would-Signal

| Value | Count |
| --- | --- |
| false | 1681 |
| true | 112 |

## Rows By Run ID

| Run ID | Rows | First Bar | Latest Bar |
| --- | --- | --- | --- |
| phase1-dry-run-v0.6 | 729 | 2026.05.22 11:00:00 | 2026.05.27 10:40:00 |
| phase1-dry-run-v0.6-daily-lock-test | 1 | 2026.05.22 12:40:00 | 2026.05.22 12:40:00 |
| phase1-dry-run-v0.6-manual-lock-test | 1 | 2026.05.22 12:40:00 | 2026.05.22 12:40:00 |
| phase1-dry-run-v0.6-monthly-lock-test | 1 | 2026.05.22 12:40:00 | 2026.05.22 12:40:00 |
| phase1-dry-run-v0.6-weekly-lock-test | 1 | 2026.05.22 12:40:00 | 2026.05.22 12:40:00 |
| phase1-dry-run-v0.7 | 1060 | 2026.05.27 10:40:00 | 2026.06.02 08:10:00 |
