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
| Phase 2 demo preflight | FAIL |
| VPS selection | PENDING |
| VPS decision check | PENDING |
| VPS latency | PENDING |
| VPS first-day verification | PENDING |
| Owner approval | PENDING |

## Wait Gates

| gate | status | current | required | remaining | unit |
| --- | --- | --- | --- | --- | --- |
| Active-market 72-hour soak | PENDING | 56.08 | 72.0 | 15.92 | hours |
| Process/code-freeze 96-hour gate | PENDING | 82.37 | 96.0 | 13.63 | hours |
| Measured cost model | PENDING | 3.0 | 5.0 | 2.0 | fresh_market_days |

## Local MT5 Network Baseline

| Field | Value |
| --- | --- |
| status | PASS |
| samples | 5757 |
| latest_ping | 174.55 ms |
| median_ping | 129.78 ms |
| best_ping | 121.76 ms |
| worst_ping | 312.50 ms |
| latest_access_point | 1 |

## VPS Selection Recommendation

| Field | Value |
| --- | --- |
| Matrix status | PENDING |
| Primary trial | FXVM Advanced VPS in Dubai, Mumbai, or Singapore |
| Backup trial | ForexVPS.net Core in the lowest-latency available region |
| Defer | QuantVPS unless broker latency testing favors US/Chicago |

Reasoning:

- FXVM Advanced meets the minimum 2 CPU / 4 GB / 60 GB requirement and offers Dubai/Mumbai/Singapore regions to test against the current broker account geography.
- ForexVPS.net Core is a clean minimum-spec alternative with stronger entry resources than FXVM Basic and an explicit 4 GB / 100 GB profile.
- QuantVPS has excellent specs but is more expensive and appears more Chicago/futures oriented, so it should not be chosen for XAU/Capital.com paper mode unless latency proves it.

Latency decision rule:

- median ping <= 50 ms: preferred
- median ping 51-100 ms: acceptable for Phase 2 paper-cost measurement
- median ping > 100 ms: owner review required
- packet loss > 0%: reject or retest before selection

## One-Screen VPS Decision Sheet

| Field | Value |
| --- | --- |
| Status | WAITING_OWNER_SELECTION |
| Decision | Select the Phase 2 VPS provider, region, and plan; do not sign owner approval yet. |
| Authority boundary | This decision only prepares VPS evidence. It does not authorize paper mode, demo trading, broker execution, or live capital. |
| Recommended first trial | FXVM Advanced VPS in Dubai, Mumbai, or Singapore |
| Backup trial | ForexVPS.net Core in the lowest-latency available region |
| Deferred option | QuantVPS unless broker latency testing favors US/Chicago |
| Decision record | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\PHASE2_VPS_SELECTION_MATRIX.md |
| Fillable template | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\templates\phase2_vps_selection_decision.template.md |
| Local baseline | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_LOCAL_MT5_NETWORK_BASELINE.md |

Required owner fields:

- Selected provider
- Selected region
- Selected plan
- Monthly cost
- Backup method
- Monitoring endpoint or scheduler
- Recovery access owner
- Decision date
- Owner acceptance that Phase 2 is paper-mode only

Latency pass preferences:

- median ping <= 50 ms: preferred
- median ping 51-100 ms: acceptable for Phase 2 paper-cost measurement
- median ping > 100 ms: owner review required
- packet loss > 0%: reject or retest before selection

After VPS is provisioned:

- Run prepare_phase2_vps_evidence_workspace.ps1 to create pending evidence files without overwriting verified evidence.
- Run capture_phase2_vps_latency_evidence.ps1 from the Phase 1 root.
- Copy and fill the vps_ntp_sync, vps_backup_config, vps_rdp_recovery, and vps_periodic_task evidence templates.
- Compile and run the Phase 1 dry-run shell only, with dry_run=true and trade_permission=false.
- Regenerate PHASE2_VPS_FIRST_DAY_VERIFICATION.md and PHASE2_READINESS_REPORT.md.

## Prepared VPS Evidence Workspace

| Field | Value |
| --- | --- |
| Status | PREPARED_PENDING_OWNER_VERIFICATION |
| Manifest | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\vps_evidence_workspace_manifest.json |
| Reports directory | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports |
| Allow overwrite verified | false |
| Authority | Evidence workspace preparation only; does not authorize Phase 2, demo trading, broker execution, live capital, or MT5 runtime changes. |

Prepared files:

| action | target | reason |
| --- | --- | --- |
| SKIPPED_EXISTING | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\vps_ntp_sync.txt | Use -Force to refresh pending template evidence. |
| SKIPPED_EXISTING | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\vps_backup_config.txt | Use -Force to refresh pending template evidence. |
| SKIPPED_EXISTING | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\vps_rdp_recovery.txt | Use -Force to refresh pending template evidence. |
| SKIPPED_EXISTING | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\vps_periodic_task.txt | Use -Force to refresh pending template evidence. |

## Owner Checklist

| step | title | status | detail |
| --- | --- | --- | --- |
| 1 | Keep local evidence collectors running | PENDING | Do not stop the Phase 1 dry-run terminal or passive spread logger while wait gates mature. |
| 2 | Select VPS provider, region, and plan | PENDING | Fill the decision record in docs/PHASE2_VPS_SELECTION_MATRIX.md with provider, region, plan, backup, recovery, monitoring, and owner acceptance. |
| 3 | Capture VPS latency evidence | PENDING | Run scripts/capture_phase2_vps_latency_evidence.ps1 from the Phase 1 root after the VPS is provisioned. |
| 4 | Fill first-day VPS verification evidence | PENDING | Copy docs/templates/vps_*.template.txt into outputs/reports, fill verified keys, then regenerate PHASE2_VPS_FIRST_DAY_VERIFICATION.md. |
| 5 | Review objective Phase 2 readiness | PENDING | Use outputs/reports/PHASE2_READINESS_REPORT.md as the sole readiness authority. |
| 6 | Sign owner approval only after all objective gates pass | PENDING | Create C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_OWNER_APPROVAL.md only after readiness is PASS. |

## Owner Approval Readiness

| Field | Value |
| --- | --- |
| Status | NOT_READY_TO_SIGN |
| Pending objective gates | 10 |
| Signing rule | Owner may sign only after every objective gate except Project owner approval is PASS. |

Objective gates still pending before owner signature:

| gate | status | evidence |
| --- | --- | --- |
| VPS selection | PENDING | `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\PHASE2_VPS_SELECTION_MATRIX.md` status is PENDING; required PASS. |
| VPS latency evidence | PENDING | `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_VPS_LATENCY_REPORT.md` status is PENDING; required PASS. |
| VPS first-day verification | PENDING | `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_VPS_FIRST_DAY_VERIFICATION.md` status is PENDING; required PASS. |
| Measured cost model | PENDING | `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase0\outputs\reports\MEASURED_COST_MODEL.md` status is PENDING; required PASS. |
| Measured-cost revalidation | PENDING | `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase0\outputs\reports\BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md` status is PENDING; required PASS. |
| Measured-cost assumption delta | PENDING | `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase0\outputs\reports\MEASURED_COST_ASSUMPTION_DELTA.md` status is PENDING; required PASS. |
| Phase 1 acceptance | PENDING | `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_ACCEPTANCE_REPORT.md` status is PENDING; required PASS. |
| Phase 1 review index | PENDING | `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_REVIEW_INDEX.md` status is PENDING; required PASS. |
| Active-market 72-hour soak | PENDING | Longest active streak 56.08h; current active streak 56.08h; required 72h; weekend policy expected_market_breaks_pause_active_market_streak. |
| Process/code-freeze 96-hour gate | PENDING | Process uptime streak 82.37h; code-freeze 82.37h; required 96h; marker 2026-05-27T10:41:50Z. |

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

### prepare_vps_evidence_workspace

```powershell
.\scripts\prepare_phase2_vps_evidence_workspace.ps1 -Phase1Root <phase1_root>
```

### generate_vps_first_day_verification

```powershell
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase2_vps_first_day_verification.py --files-dir C:\MT5PortableGoldMission\MQL5\Files --compile-log C:\MT5PortableGoldMission\compile_Phase1DryRunShell.log --scheduler-evidence outputs\reports\vps_periodic_task.txt
```

### capture_vps_latency

```powershell
.\scripts\capture_phase2_vps_latency_evidence.ps1 -Provider "<provider>" -Region "<region>" -Endpoint "<broker_or_mt5_endpoint>" -SampleCount 20
```

### check_vps_selection_decision

```powershell
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase2_vps_selection_decision_check.py
```

### install_periodic_checks_task_dry_run

```powershell
.\scripts\install_phase2_periodic_checks_task.ps1 -Phase1Root <phase1_root> -PythonExe <phase0_python_exe> -FilesDir <mt5_files_dir> -SpreadFilesDir <spread_logger_files_dir> -CompileLog <compile_log_path> -IntervalMinutes 60 -Provider <selected_provider> -Region <selected_region> -WriteEvidence -WhatIfOnly
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
| local_mt5_network_baseline | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_LOCAL_MT5_NETWORK_BASELINE.md |
| vps_evidence_workspace_manifest | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\vps_evidence_workspace_manifest.json |
| vps_first_day_verification | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_VPS_FIRST_DAY_VERIFICATION.md |
| vps_selection_decision_check | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_VPS_SELECTION_DECISION_CHECK.md |
| vps_selection_matrix | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\PHASE2_VPS_SELECTION_MATRIX.md |
| owner_approval_draft | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\PHASE2_OWNER_APPROVAL_DRAFT.md |
| phase2_demo_transition_runbook | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\PHASE2_DEMO_TRANSITION_RUNBOOK.md |
