# Phase 2 VPS Bootstrap Packet

This packet is an operational VPS bootstrap handoff only. It does not authorize Phase 2, demo trading, broker execution, live capital, or paper-mode implementation.

Overall status: WAITING_AND_VPS_BOOTSTRAP_PENDING

## Authority

| Field | Value |
| --- | --- |
| Paper mode authorized | false |
| Demo trading authorized | false |
| Broker execution authorized | false |
| Live trading authorized | false |

## Source Status

| Field | Value |
| --- | --- |
| phase2_readiness | PENDING |
| phase2_demo_preflight | PENDING |
| phase2_demo_countdown | DEMO_NOT_READY |
| phase2_owner_action_packet | WAITING_AND_OWNER_ACTION_REQUIRED |
| vps_selection | PENDING |
| vps_latency | PENDING |
| vps_first_day_verification | PENDING |
| project_owner_approval | PENDING |

## Runtime Snapshot

| Field | Value |
| --- | --- |
| decision_rows | 1060 |
| latest_bar | 2026.05.28 14:50:00 |
| dry_run | true |
| trade_permission | false |
| server_time_status | CLOCK_OK |

## Wait Gates

| gate | status | current | required | remaining | unit |
| --- | --- | --- | --- | --- | --- |
| Active-market 72-hour soak | PENDING | 27.08 | 72.0 | 44.92 | hours |
| Process/code-freeze 96-hour gate | PENDING | 28.22 | 96.0 | 67.78 | hours |
| Measured cost model | PENDING | 2.0 | 5.0 | 3.0 | fresh_market_days |

## Owner Actions Now

| gate | status | action |
| --- | --- | --- |
| VPS selection | PENDING | Owner selects provider/region/plan from PHASE2_VPS_SELECTION_MATRIX.md. |
| VPS latency evidence | PENDING | After VPS is provisioned, run scripts/capture_phase2_vps_latency_evidence.ps1 from the Phase 1 root. |
| VPS first-day verification | PENDING | After VPS setup, capture NTP, backup, recovery-login, periodic scheduler, MT5 path, compile, startup, decision, and health evidence. |
| Project owner approval | PENDING | Sign PHASE2_OWNER_APPROVAL.md only after all objective gates are PASS. |

## Bootstrap Phases

### Before VPS Purchase

Choose the VPS without touching the local MT5 runtime.

Steps:
- Keep the local Phase 1 dry-run shell and passive spread logger running.
- Fill docs/PHASE2_VPS_SELECTION_MATRIX.md with provider, region, plan, backup, recovery, monitoring, and owner decision fields.
- Do not create PHASE2_OWNER_APPROVAL.md until PHASE2_READINESS_REPORT.md is PASS.

Evidence:
- C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\PHASE2_VPS_SELECTION_MATRIX.md
- C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\templates\phase2_vps_selection_decision.template.md

### On VPS First Login

Capture environment and latency evidence before any paper-mode work.

Steps:
- Clone or copy the repository to the VPS and keep secrets out of tracked files.
- Install or copy MT5 Portable in dry-run configuration only.
- Run the 20-sample latency capture against the broker or MT5 endpoint.
- Copy the NTP, backup, RDP recovery, and periodic-task templates into outputs/reports and fill only verified values.

Evidence:
- C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_VPS_LATENCY_REPORT.md
- C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\vps_ntp_sync.txt
- C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\vps_backup_config.txt
- C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\vps_rdp_recovery.txt
- C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\vps_periodic_task.txt

### After MT5 Dry-Run Deploy

Prove the VPS can run the dry-run shell safely before demo trading exists.

Steps:
- Compile the Phase 1 dry-run shell and preserve the compile log.
- Start MT5 with dry_run=true and trade_permission=false.
- Confirm decision_log.csv receives rows and the dashboard/runtime health remain green.
- Generate PHASE2_VPS_FIRST_DAY_VERIFICATION.md from VPS evidence.

Evidence:
- C:\MT5PortableGoldMission\compile_Phase1DryRunShell.log
- C:\MT5PortableGoldMission\MQL5\Files\decision_log.csv
- C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_VPS_FIRST_DAY_VERIFICATION.md

### Before Owner Approval

Confirm objective gates before any paper-mode implementation.

Steps:
- Run scripts/run_phase1_periodic_checks.py with the VPS MT5 Files directory and passive spread Files directory.
- Install or verify the Windows Task Scheduler entry for periodic checks.
- Verify PHASE2_READINESS_REPORT.md and PHASE2_DEMO_PREFLIGHT_REPORT.md are PASS.
- Verify PHASE2_DEMO_COUNTDOWN.md has zero pending gates.
- Only then create outputs/reports/PHASE2_OWNER_APPROVAL.md.

Evidence:
- C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_READINESS_REPORT.md
- C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_DEMO_PREFLIGHT_REPORT.md
- C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_DEMO_COUNTDOWN.md
- C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_OWNER_APPROVAL.md
- C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\scripts\install_phase2_periodic_checks_task.ps1

## Commands

### refresh_local_readiness

```powershell
..\xauusd-phase0\.venv\Scripts\python.exe scripts\run_phase1_periodic_checks.py --files-dir C:\MT5PortableGoldMission\MQL5\Files --spread-files-dir C:\MT5PortableSpreadLogger\MQL5\Files
```

### capture_vps_latency

```powershell
.\scripts\capture_phase2_vps_latency_evidence.ps1 -Provider "<provider>" -Region "<region>" -Endpoint "<broker_or_mt5_endpoint>" -SampleCount 20
```

### copy_vps_evidence_templates

```powershell
Copy-Item docs\templates\vps_ntp_sync.template.txt outputs\reports\vps_ntp_sync.txt
Copy-Item docs\templates\vps_backup_config.template.txt outputs\reports\vps_backup_config.txt
Copy-Item docs\templates\vps_rdp_recovery.template.txt outputs\reports\vps_rdp_recovery.txt
Copy-Item docs\templates\vps_periodic_task.template.txt outputs\reports\vps_periodic_task.txt
```

### generate_vps_first_day_verification

```powershell
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase2_vps_first_day_verification.py --files-dir C:\MT5PortableGoldMission\MQL5\Files --compile-log C:\MT5PortableGoldMission\compile_Phase1DryRunShell.log --scheduler-evidence outputs\reports\vps_periodic_task.txt
```

### generate_bootstrap_packet

```powershell
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase2_vps_bootstrap_packet.py
```

### install_periodic_checks_task

```powershell
.\scripts\install_phase2_periodic_checks_task.ps1 -Phase1Root <phase1_root> -PythonExe <phase0_python_exe> -FilesDir <mt5_files_dir> -SpreadFilesDir <spread_logger_files_dir> -CompileLog <compile_log_path> -IntervalMinutes 60 -WhatIfOnly
```

## Evidence Paths

| evidence | path |
| --- | --- |
| vps_selection_matrix | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\PHASE2_VPS_SELECTION_MATRIX.md |
| vps_selection_decision_template | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\templates\phase2_vps_selection_decision.template.md |
| vps_latency_report | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_VPS_LATENCY_REPORT.md |
| vps_first_day_verification | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_VPS_FIRST_DAY_VERIFICATION.md |
| phase2_readiness | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_READINESS_REPORT.md |
| phase2_owner_approval | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_OWNER_APPROVAL.md |

## Source Reports

| report | path |
| --- | --- |
| phase2_demo_countdown | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_DEMO_COUNTDOWN.json |
| phase2_owner_action_packet | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_OWNER_ACTION_PACKET.json |
| phase2_readiness | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_READINESS_REPORT.md |
| phase2_demo_preflight | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_DEMO_PREFLIGHT_REPORT.md |
| vps_selection_matrix | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\PHASE2_VPS_SELECTION_MATRIX.md |
| vps_latency_report | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_VPS_LATENCY_REPORT.md |
| vps_first_day_verification | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_VPS_FIRST_DAY_VERIFICATION.md |
| phase1_status_summary | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_STATUS_SUMMARY.json |
