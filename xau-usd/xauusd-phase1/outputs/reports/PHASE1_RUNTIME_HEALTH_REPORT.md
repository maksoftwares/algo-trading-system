# Phase 1 Runtime Health Report

Overall status: WARN

Files directory: `C:\MT5PortableGoldMission\MQL5\Files`

## Checks

| Check | Status | Message |
| --- | --- | --- |
| decision_log | PASS | Found `C:\MT5PortableGoldMission\MQL5\Files\decision_log.csv` (4577 bytes). |
| startup_log | PASS | Found `C:\MT5PortableGoldMission\MQL5\Files\startup_log.csv` (682 bytes). |
| shutdown_log | PASS | Found `C:\MT5PortableGoldMission\MQL5\Files\shutdown_log.csv` (2066 bytes). |
| decision_rows | PASS | Decision rows: 4. |
| latest_freshness | PASS | Latest row age is 0.3 minute(s); limit 15. |
| dry_run_lock | PASS | All decision rows stayed dry-run. |
| permission_lock | PASS | All decision rows kept permission false. |
| server_time_status | PASS | All rows report CLOCK_OK. |
| exact_duplicate_rows | PASS | No exact duplicate runtime rows found. |
| unique_bar_gaps | PASS | Unique bar sequence has no larger-than-M5 gaps. |
| startup_shutdown_rows | WARN | Shutdown rows exceed startup rows: 13 > 2. |

## Runtime Shape

- Decision rows: 4
- Startup rows: 2
- Shutdown rows: 13
- Unique run IDs: 1
- First unique M5 bar: 2026.05.22 11:00:00
- Latest unique M5 bar: 2026.05.22 11:10:00
- Larger-than-M5 gaps: 0
- Expected market-break gaps: 0

## Latest Row

| Run ID | Broker Time | Local Time | Bar Time | Dry Run | Permission | Server Time | BR Stage |
| --- | --- | --- | --- | --- | --- | --- | --- |
| phase1-dry-run-v0.6 | 2026.05.22 11:10:00 | 2026.05.22 15:09:57 | 2026.05.22 11:10:00 | true | false | CLOCK_OK | WAIT_LEVEL_BREAK_RETEST |

## Recent Gaps

No rows.

## Rows By Run ID

| Run ID | Rows | First Bar | Latest Bar |
| --- | --- | --- | --- |
| phase1-dry-run-v0.6 | 4 | 2026.05.22 11:00:00 | 2026.05.22 11:10:00 |
