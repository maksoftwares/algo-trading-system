# Shutdown Resume Checkpoint

Date: 2026-05-31

Purpose: document the intentional workstation shutdown after the Phase 1 process/code-freeze evidence crossed 96 hours. This checkpoint is informational and does not authorize Phase 2, paper-mode execution, broker-side execution, or live trading.

## Pre-Shutdown State

| Area | Status |
| --- | --- |
| Phase 1 periodic checks | PASS at last refresh |
| Phase 1 acceptance | PENDING |
| Phase 2 readiness | PENDING |
| Phase 2 demo preflight | FAIL / DEMO_NOT_READY |
| Phase 1 dry-run boundary | PASS: `dry_run=true`, `trade_permission=false`, `server_time_status=CLOCK_OK` |
| Latest Phase 1 bar | `2026.05.29 20:55:00` broker time |
| Decision rows | `1407` |
| Active-market 72-hour streak | `56.08h / 72h` PENDING |
| Process/code-freeze 96-hour gate | PASS: `96.01h / 96h` |
| Five trading day soak | PASS |
| Measured cost model | PENDING |
| Fresh measured-cost days | `3 / 5`: 2026-05-27, 2026-05-28, 2026-05-29 |
| Fresh measured spread rows | `50006` |
| Median / P95 / max spread | `50 / 75 / 180` points |

## Evidence Captured Before Shutdown

The 96-hour process/code-freeze gate has already been captured as PASS in these artifacts:

| Artifact | Evidence |
| --- | --- |
| `xau-usd/xauusd-phase1/outputs/reports/PHASE1_STATUS_SUMMARY.json` | `process_code_freeze_pass=true`, `process_uptime_streak_hours=96.01`, `code_freeze_hours=96.01` |
| `xau-usd/xauusd-phase1/outputs/reports/PHASE1_ACCEPTANCE_REPORT.md` | `Process/code-freeze 96-hour gate` = PASS |
| `xau-usd/xauusd-phase1/outputs/reports/PHASE2_READINESS_REPORT.md` | `Process/code-freeze 96-hour gate` = PASS |
| `status.html` | 96h freeze gate PASS and wait-gate remaining time `0.0` hours |

After a shutdown, any newly restarted MT5 process uptime will begin from zero. That must not be interpreted as erasing the captured 96-hour PASS evidence above; it only means a future fresh runtime will have a new process start time.

## Running Local Components Observed

| Component | Path |
| --- | --- |
| Phase 1 dry-run terminal | `C:\MT5PortableGoldMission\terminal64.exe` |
| Passive spread logger terminal | `C:\MT5PortableSpreadLogger\terminal64.exe` |
| User MT5 terminal | `C:\Program Files\MetaTrader 5\terminal64.exe` |
| Phase 1 runtime files | `C:\MT5PortableGoldMission\MQL5\Files` |
| Spread logger files | `C:\MT5PortableSpreadLogger\MQL5\Files` |

## Shutdown Effect

| Gate or process | Effect of shutdown |
| --- | --- |
| Passive spread logging | Pauses while the machine is off. This is acceptable during the weekend because no fresh market day is expected while XAU/FX is closed. |
| Measured cost model | Remains PENDING until two more fresh market days are observed after market resume. |
| Active-market 72-hour streak | Weekend market-break gaps are expected pauses and should not add closed-market time. Resume near market open to continue collecting active-market evidence. |
| Process/code-freeze 96-hour gate | Captured as PASS before shutdown. A restarted MT5 process will have fresh uptime, but the pre-shutdown PASS evidence remains in the reports listed above. |
| Phase 1 acceptance | Remains PENDING until the active-market 72-hour gate and all other acceptance gates are PASS. |
| Phase 2 readiness | Remains PENDING. Shutdown does not authorize Phase 2 paper-mode implementation. |
| Phase 3 experimental package | Remains frozen/review-only. No runtime authority. |

## Before Shutdown

1. Use the standard Windows shutdown flow when ready.
2. Do not manually change EA settings, presets, charts, or terminal files before shutting down.
3. Do not treat the off-machine gap as active-market evidence.
4. On the next resume, refresh reports before making any Phase 2 decision.

## Monday Resume Procedure

Target resume: Monday 2026-06-01 near broker/FX/XAU market open. In India time, the common FX/XAU reopen window is around `02:30 IST`, but broker-specific availability may vary.

After Windows is back online, start or confirm both portable terminals:

```powershell
C:\MT5PortableGoldMission\terminal64.exe /portable /config:C:\MT5PortableGoldMission\Config\phase1_dry_run_startup.ini
C:\MT5PortableSpreadLogger\terminal64.exe /portable /config:C:\MT5PortableSpreadLogger\Config\phase0_spread_logger_startup.ini
```

Then refresh reports:

```powershell
cd "C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1"
..\xauusd-phase0\.venv\Scripts\python.exe scripts\run_phase1_periodic_checks.py --files-dir C:\MT5PortableGoldMission\MQL5\Files --spread-files-dir C:\MT5PortableSpreadLogger\MQL5\Files --compile-log C:\MT5PortableGoldMission\compile_Phase1DryRunShell.log
```

Confirm:

| Check | Expected |
| --- | --- |
| Periodic checks | PASS or weekend/open-transition warning only |
| Latest dry-run row | Fresh after market data resumes |
| `dry_run` | `true` |
| `trade_permission` | `false` |
| `server_time_status` | `CLOCK_OK` |
| Phase 1 acceptance | PENDING until active-market and remaining gates pass |
| Process/code-freeze 96-hour gate | PASS evidence remains captured; do not require the restarted process to show 96h immediately |
| Measured cost model | PENDING until `5 / 5` fresh observed market days pass |
| Phase 2 readiness | PENDING until all objective gates and owner approval pass |

## Boundary

- Phase 1 remains dry-run only.
- Passive spread logging remains observation-only.
- Phase 2 remains preparation only.
- Phase 3 remains review-only/frozen.
- No broker-side execution or live trading is authorized.
