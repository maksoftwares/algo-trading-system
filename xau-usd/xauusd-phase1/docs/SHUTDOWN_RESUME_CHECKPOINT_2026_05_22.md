# Shutdown Resume Checkpoint

Date: 2026-05-22

Purpose: document the intentional one-day workstation shutdown so Phase 1 soak, passive spread logging, and Phase 2 readiness are resumed cleanly.

## Current Pre-Shutdown State

| Area | Status |
| --- | --- |
| Phase 1 periodic checks | PASS |
| Phase 1 acceptance | PENDING |
| Phase 2 readiness | PENDING |
| Phase 1 dry-run boundary | PASS: `dry_run=true`, `trade_permission=false`, `server_time_status=CLOCK_OK` |
| Latest Phase 1 bar | `2026.05.22 14:55:00` broker time |
| Phase 1 soak progress | `3.26%`, `0.1632 / 5.00` required days |
| Decision rows | `54` |
| Would-signal evidence | `10` rows, `10` clusters |
| Measured cost model | PENDING |
| Measured spread rows | `5595` rows |
| Measured spread days | `1 / 5` required days |
| Median / P95 / max spread | `50 / 75 / 75` points |

## Running Local Components

| Component | Path |
| --- | --- |
| Phase 1 dry-run terminal | `C:\MT5PortableGoldMission\terminal64.exe` |
| Passive spread logger terminal | `C:\MT5PortableSpreadLogger\terminal64.exe` |
| Phase 1 runtime files | `C:\MT5PortableGoldMission\MQL5\Files` |
| Spread logger files | `C:\MT5PortableSpreadLogger\MQL5\Files` |

## What Will Pause

The following gates depend on the machine being on, MT5 connected, and local files being updated:

| Gate | Effect of shutdown |
| --- | --- |
| Five-trading-day Phase 1 soak | Pauses. The elapsed off-time must not be counted as observed soak. |
| Passive spread logger | Pauses. Measured cost model will remain PENDING until enough connected days are observed. |
| Hourly local automation | Paused intentionally before shutdown to avoid noisy failures while the machine is off. |
| Phase 2 readiness | Remains PENDING until measured cost, measured-cost revalidation, five-day soak, review index, and owner approval pass. |

## Before Shutdown

1. Keep both MT5 instances in their current dry-run/passive state until the owner is ready to power down.
2. If shutting down normally, close Windows through the standard shutdown flow. No live orders or broker-side actions are enabled.
3. Do not treat the shutdown gap as soak evidence.

## Resume Procedure

After the machine is back online:

```powershell
cd "C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1"
..\xauusd-phase0\.venv\Scripts\python.exe scripts\run_phase1_periodic_checks.py --files-dir C:\MT5PortableGoldMission\MQL5\Files --spread-files-dir C:\MT5PortableSpreadLogger\MQL5\Files --compile-log C:\MT5PortableGoldMission\compile_Phase1DryRunShell.log
```

Then confirm:

| Check | Expected |
| --- | --- |
| Periodic checks | PASS |
| Latest dry-run row | Fresh after restart |
| `dry_run` | `true` |
| `trade_permission` | `false` |
| `server_time_status` | `CLOCK_OK` |
| Phase 1 acceptance | PENDING until five connected trading days pass |
| Measured cost model | PENDING until five observed spread days pass |

## Automation Resume

The local automation `phase1-mt5-soak-check` was paused for shutdown. Re-enable it after the machine and both MT5 terminals are running again.

Do not advance Phase 2 until:

```text
Phase 1 acceptance = PASS
Measured cost model = PASS
Measured-cost revalidation = PASS
Phase 1 review index = PASS
Phase 2 readiness = PASS
Owner approval = PASS
```

## Boundary

This shutdown does not change the project state:

- Phase 1 remains dry-run only.
- Phase 2 remains preparation only.
- No live broker action is authorized.
- `breakout_retest` and `swing_breakout_retest_v0` remain one same-family breakout-retest edge family for risk planning.
