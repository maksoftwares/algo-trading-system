# Phase 2 Owner Action Packet

This packet is an owner handoff only. It does not authorize Phase 2, demo trading, broker execution, live capital, or any paper-mode implementation.

Overall status: WAITING_AND_OWNER_ACTION_REQUIRED

## Authority

| Field | Value |
| --- | --- |
| Paper mode authorized | false |
| Demo trading authorized | false |
| Broker execution authorized | false |
| Live trading authorized | false |

## Current Status

| Field | Value |
| --- | --- |
| Phase 2 readiness | PENDING |
| Phase 2 demo preflight | PENDING |
| VPS selection | PENDING |
| VPS latency | PENDING |
| VPS first-day verification | PENDING |
| Owner approval | PENDING |

## Wait Gates

| gate | status | current | required | remaining | unit |
| --- | --- | --- | --- | --- | --- |
| Active-market 72-hour soak | PENDING | 27.33 | 72.0 | 44.67 | hours |
| Process/code-freeze 96-hour gate | PENDING | 28.47 | 96.0 | 67.53 | hours |
| Measured cost model | PENDING | 2.0 | 5.0 | 3.0 | fresh_market_days |

## Owner Checklist

| step | title | status | detail |
| --- | --- | --- | --- |
| 1 | Keep local evidence collectors running | PENDING | Do not stop the Phase 1 dry-run terminal or passive spread logger while wait gates mature. |
| 2 | Select VPS provider, region, and plan | PENDING | Fill the decision record in docs/PHASE2_VPS_SELECTION_MATRIX.md with provider, region, plan, backup, recovery, monitoring, and owner acceptance. |
| 3 | Capture VPS latency evidence | PENDING | Run scripts/capture_phase2_vps_latency_evidence.ps1 from the Phase 1 root after the VPS is provisioned. |
| 4 | Fill first-day VPS verification evidence | PENDING | Copy docs/templates/vps_*.template.txt into outputs/reports, fill verified keys, then regenerate PHASE2_VPS_FIRST_DAY_VERIFICATION.md. |
| 5 | Review objective Phase 2 readiness | PENDING | Use outputs/reports/PHASE2_READINESS_REPORT.md as the sole readiness authority. |
| 6 | Sign owner approval only after all objective gates pass | PENDING | Create C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_OWNER_APPROVAL.md only after readiness is PASS. |

## Immediate Owner Actions

| gate | status | action |
| --- | --- | --- |
| VPS selection | PENDING | Owner selects provider/region/plan from PHASE2_VPS_SELECTION_MATRIX.md. |
| VPS latency evidence | PENDING | After VPS is provisioned, run scripts/capture_phase2_vps_latency_evidence.ps1 from the Phase 1 root. |
| VPS first-day verification | PENDING | After VPS setup, capture NTP, backup, recovery-login, periodic scheduler, MT5 path, compile, startup, decision, and health evidence. |
| Project owner approval | PENDING | Sign PHASE2_OWNER_APPROVAL.md only after all objective gates are PASS. |

## Commands

### refresh_readiness

```powershell
..\xauusd-phase0\.venv\Scripts\python.exe scripts\run_phase1_periodic_checks.py --files-dir C:\MT5PortableGoldMission\MQL5\Files --spread-files-dir C:\MT5PortableSpreadLogger\MQL5\Files
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

### capture_vps_latency

```powershell
.\scripts\capture_phase2_vps_latency_evidence.ps1 -Provider "<provider>" -Region "<region>" -Endpoint "<broker_or_mt5_endpoint>" -SampleCount 20
```

### install_periodic_checks_task_dry_run

```powershell
.\scripts\install_phase2_periodic_checks_task.ps1 -Phase1Root <phase1_root> -PythonExe <phase0_python_exe> -FilesDir <mt5_files_dir> -SpreadFilesDir <spread_logger_files_dir> -CompileLog <compile_log_path> -IntervalMinutes 60 -WhatIfOnly
```

## Owner Templates

| template | path |
| --- | --- |
| vps_selection_decision | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\templates\phase2_vps_selection_decision.template.md |
| vps_ntp_sync | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\templates\vps_ntp_sync.template.txt |
| vps_backup_config | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\templates\vps_backup_config.template.txt |
| vps_rdp_recovery | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\templates\vps_rdp_recovery.template.txt |
| vps_periodic_task | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\templates\vps_periodic_task.template.txt |

## Source Reports

| report | path |
| --- | --- |
| phase2_demo_countdown | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_DEMO_COUNTDOWN.json |
| phase2_readiness | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_READINESS_REPORT.md |
| phase2_demo_preflight | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_DEMO_PREFLIGHT_REPORT.md |
| phase2_vps_bootstrap | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_VPS_BOOTSTRAP_PACKET.md |
| vps_first_day_verification | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_VPS_FIRST_DAY_VERIFICATION.md |
| vps_selection_matrix | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\PHASE2_VPS_SELECTION_MATRIX.md |
| owner_approval_draft | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\PHASE2_OWNER_APPROVAL_DRAFT.md |
