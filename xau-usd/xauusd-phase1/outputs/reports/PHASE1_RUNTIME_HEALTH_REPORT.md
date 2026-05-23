# Phase 1 Runtime Health Report

Overall status: PASS

Files directory: `C:\MT5PortableGoldMission\MQL5\Files`

## Checks

| Check | Status | Message |
| --- | --- | --- |
| decision_log | PASS | Found `C:\MT5PortableGoldMission\MQL5\Files\decision_log.csv` (46932 bytes). |
| startup_log | PASS | Found `C:\MT5PortableGoldMission\MQL5\Files\startup_log.csv` (1898 bytes). |
| shutdown_log | PASS | Found `C:\MT5PortableGoldMission\MQL5\Files\shutdown_log.csv` (2204 bytes). |
| decision_rows | PASS | Decision rows: 56. |
| latest_freshness | PASS | Latest row age is 83.4 minute(s), but local date is a weekend market break; runtime freshness is paused. |
| dry_run_lock | PASS | All decision rows stayed dry-run. |
| permission_lock | PASS | All decision rows kept permission false. |
| server_time_status | PASS | Latest row reports CLOCK_OK; historical non-CLOCK_OK rows: 1. |
| exact_duplicate_rows | PASS | No exact duplicate runtime rows found. |
| unique_bar_gaps | PASS | Only expected market-break gaps found: 1. |
| startup_shutdown_rows | PASS | Startup and shutdown logs are both present; shutdown rows exceed startup rows (14 > 9) after restart/test cycles. |

## Runtime Shape

- Decision rows: 56
- Startup rows: 9
- Shutdown rows: 14
- Unique run IDs: 5
- First unique M5 bar: 2026.05.22 11:00:00
- Latest unique M5 bar: 2026.05.22 20:55:00
- Larger-than-M5 gaps: 0
- Expected market-break gaps: 1

## Latest Row

| Run ID | Broker Time | Local Time | Bar Time | Dry Run | Permission | Server Time | BR Stage |
| --- | --- | --- | --- | --- | --- | --- | --- |
| phase1-dry-run-v0.6 | 2026.05.23 12:18:20 | 2026.05.23 17:48:29 | 2026.05.22 20:55:00 | true | false | CLOCK_OK | WAIT_LEVEL_BREAK_RETEST |

## Recent Gaps

No rows.

## Rows By Run ID

| Run ID | Rows | First Bar | Latest Bar |
| --- | --- | --- | --- |
| phase1-dry-run-v0.6 | 52 | 2026.05.22 11:00:00 | 2026.05.22 20:55:00 |
| phase1-dry-run-v0.6-daily-lock-test | 1 | 2026.05.22 12:40:00 | 2026.05.22 12:40:00 |
| phase1-dry-run-v0.6-manual-lock-test | 1 | 2026.05.22 12:40:00 | 2026.05.22 12:40:00 |
| phase1-dry-run-v0.6-monthly-lock-test | 1 | 2026.05.22 12:40:00 | 2026.05.22 12:40:00 |
| phase1-dry-run-v0.6-weekly-lock-test | 1 | 2026.05.22 12:40:00 | 2026.05.22 12:40:00 |
