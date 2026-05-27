# Phase 1 Acceptance Report

Overall status: PENDING

Files directory: `C:\MT5PortableGoldMission\MQL5\Files`

## Acceptance Gates

| Gate | Status | Evidence |
| --- | --- | --- |
| MT5 compile | PASS | Compile log passed: `C:\MT5PortableGoldMission\compile_Phase1DryRunShell.log` |
| Source safety audit | PASS | No findings under `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1`. |
| Runtime log verification | WARN | Report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_DRY_RUN_LOG_REPORT.md` |
| Soak/drift analysis | WARN | Report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_DRIFT_REPORT.md` |
| Runtime health | WARN | Report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_RUNTIME_HEALTH_REPORT.md` |
| Would-signal evidence | PASS | Rows: 74; clusters: 74; report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_WOULD_SIGNAL_REPORT.md`; csv: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_WOULD_SIGNAL_REVIEW.csv` |
| Soak history ledger | WARN | History report has warnings: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY_REPORT.md` |
| Dry-run state | PASS | All decision rows are in dry-run state. |
| Permission lock | PASS | All decision rows keep permission false. |
| Runtime freshness | PASS | Latest row age is 1.1 minute(s); limit 15. |
| Latest runtime row | PASS | run_id=phase1-dry-run-v0.6; bar_time=2026.05.27 09:35:00; risk=NORMAL; server_time=CLOCK_OK; observer=WAIT_LEVEL_BREAK_RETEST/LONG; would_signal=false |
| Active-market 72-hour soak | PENDING | Longest active streak: 22.92h; current active streak: 11.58h; required: 72h; last restart UTC: 2026-05-22T11:03:44Z; weekend policy: weekend_breaks_active_market_streak. |
| Process/code-freeze 96-hour gate | PENDING | Process uptime streak: 118.54h; code-freeze hours: 9.08h; required: 96h; marker: 2026-05-27T00:31:23Z; marker path: `C:\MT5PortableGoldMission\MQL5\Files\phase1_code_freeze_started_at.txt`. |
| Five trading day soak | PENDING | Observed unique-bar span: 4.94 calendar day(s), from 2026-05-22 11:00:00 to 2026-05-27 09:35:00. |

## Decision

Phase 1 is progressing, but final acceptance remains pending until the required wall-clock soak is complete.

## Runtime Rows

- Decision rows analyzed: 720
- Unique run IDs: 5
