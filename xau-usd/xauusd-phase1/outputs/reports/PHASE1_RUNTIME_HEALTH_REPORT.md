# Phase 1 Runtime Health Report

Overall status: PASS

Files directory: `C:\MT5PortableGoldMission\MQL5\Files`

## Checks

| Check | Status | Message |
| --- | --- | --- |
| decision_log | PASS | Found `C:\MT5PortableGoldMission\MQL5\Files\decision_log.csv` (119988 bytes). |
| startup_log | PASS | Found `C:\MT5PortableGoldMission\MQL5\Files\startup_log.csv` (2817 bytes). |
| shutdown_log | PASS | Found `C:\MT5PortableGoldMission\MQL5\Files\shutdown_log.csv` (2066 bytes). |
| decision_rows | PASS | Decision rows: 182. |
| latest_freshness | PASS | Latest row age is 3.9 minute(s); limit 15. |
| dry_run_lock | PASS | All decision rows stayed dry-run. |
| permission_lock | PASS | All decision rows kept permission false. |
| server_time_status | PASS | All rows report CLOCK_OK. |
| exact_duplicate_rows | PASS | No exact duplicate runtime rows found. |
| unique_bar_gaps | PASS | Only expected market-break gaps found: 1. |
| startup_shutdown_rows | PASS | Startup rows: 15; shutdown rows: 13. |

## Runtime Shape

- Decision rows: 182
- Startup rows: 15
- Shutdown rows: 13
- Unique run IDs: 5
- First unique M5 bar: 2026.05.21 13:45:00
- Latest unique M5 bar: 2026.05.22 05:25:00
- Larger-than-M5 gaps: 0
- Expected market-break gaps: 1

## Latest Row

| Run ID | Broker Time | Local Time | Bar Time | Dry Run | Permission | Server Time | BR Stage |
| --- | --- | --- | --- | --- | --- | --- | --- |
| phase1-dry-run-v0.5 | 2026.05.22 05:25:00 | 2026.05.22 09:24:57 | 2026.05.22 05:25:00 | true | false | CLOCK_OK | WAIT_LEVEL_BREAK_RETEST |

## Recent Gaps

No rows.

## Rows By Run ID

| Run ID | Rows | First Bar | Latest Bar |
| --- | --- | --- | --- |
| phase1-dry-run-v0.5 | 178 | 2026.05.21 13:45:00 | 2026.05.22 05:25:00 |
| phase1-dry-run-v0.5-daily-lock-test | 1 | 2026.05.21 13:50:00 | 2026.05.21 13:50:00 |
| phase1-dry-run-v0.5-manual-lock-test | 1 | 2026.05.21 13:50:00 | 2026.05.21 13:50:00 |
| phase1-dry-run-v0.5-monthly-lock-test | 1 | 2026.05.21 13:50:00 | 2026.05.21 13:50:00 |
| phase1-dry-run-v0.5-weekly-lock-test | 1 | 2026.05.21 13:50:00 | 2026.05.21 13:50:00 |
