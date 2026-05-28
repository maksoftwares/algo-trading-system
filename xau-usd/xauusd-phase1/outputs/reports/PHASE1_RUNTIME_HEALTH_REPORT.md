# Phase 1 Runtime Health Report

Overall status: PASS

Files directory: `C:\MT5PortableGoldMission\MQL5\Files`

## Checks

| Check | Status | Message |
| --- | --- | --- |
| decision_log | PASS | Found `C:\MT5PortableGoldMission\MQL5\Files\decision_log.csv` (967193 bytes). |
| startup_log | PASS | Found `C:\MT5PortableGoldMission\MQL5\Files\startup_log.csv` (1373 bytes). |
| shutdown_log | PASS | Found `C:\MT5PortableGoldMission\MQL5\Files\shutdown_log.csv` (2204 bytes). |
| decision_rows | PASS | Decision rows: 1043. |
| latest_freshness | PASS | Latest row age is 3.0 minute(s); limit 15. |
| dry_run_lock | PASS | All decision rows stayed dry-run. |
| permission_lock | PASS | All decision rows kept permission false. |
| server_time_status | PASS | Latest row reports CLOCK_OK; historical non-CLOCK_OK rows: 1. |
| exact_duplicate_rows | PASS | No exact duplicate runtime rows found. |
| unique_bar_gaps | PASS | Only expected market-break gaps found: 5. |
| startup_shutdown_rows | PASS | Startup and shutdown logs are both present; shutdown rows exceed startup rows (14 > 3) after restart/test cycles. |

## Runtime Shape

- Decision rows: 1043
- Startup rows: 3
- Shutdown rows: 14
- Unique run IDs: 6
- First unique M5 bar: 2026.05.22 11:00:00
- Latest unique M5 bar: 2026.05.28 13:25:00
- Larger-than-M5 gaps: 0
- Expected market-break gaps: 5

## Latest Row

| Run ID | Broker Time | Local Time | Bar Time | Dry Run | Permission | Server Time | BR Stage |
| --- | --- | --- | --- | --- | --- | --- | --- |
| phase1-dry-run-v0.7 | 2026.05.28 13:25:00 | 2026.05.28 18:55:00 | 2026.05.28 13:25:00 | true | false | CLOCK_OK | WAIT_LEVEL_BREAK_RETEST |

## Recent Gaps

No rows.

## Rows By Run ID

| Run ID | Rows | First Bar | Latest Bar |
| --- | --- | --- | --- |
| phase1-dry-run-v0.6 | 729 | 2026.05.22 11:00:00 | 2026.05.27 10:40:00 |
| phase1-dry-run-v0.6-daily-lock-test | 1 | 2026.05.22 12:40:00 | 2026.05.22 12:40:00 |
| phase1-dry-run-v0.6-manual-lock-test | 1 | 2026.05.22 12:40:00 | 2026.05.22 12:40:00 |
| phase1-dry-run-v0.6-monthly-lock-test | 1 | 2026.05.22 12:40:00 | 2026.05.22 12:40:00 |
| phase1-dry-run-v0.6-weekly-lock-test | 1 | 2026.05.22 12:40:00 | 2026.05.22 12:40:00 |
| phase1-dry-run-v0.7 | 310 | 2026.05.27 10:40:00 | 2026.05.28 13:25:00 |
