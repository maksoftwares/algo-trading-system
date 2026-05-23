# Resume Checkpoint - 2026-05-23

## Scope

This checkpoint records the post-shutdown restart for the Phase 1 MT5 dry-run shell and the passive spread logger.

## Restart Actions

- Started `C:\MT5PortableGoldMission\terminal64.exe` with `/portable /config:C:\MT5PortableGoldMission\Config\phase1_dry_run_startup.ini`.
- Started `C:\MT5PortableSpreadLogger\terminal64.exe` with `/portable /config:C:\MT5PortableSpreadLogger\Config\phase0_spread_logger_startup.ini`.
- Confirmed both terminal processes are running from the intended portable roots.
- Confirmed `Phase1DryRunShell.mq5` is attached and writing to `C:\MT5PortableGoldMission\MQL5\Files\decision_log.csv`.

## Timezone Correction

The machine is now on India Standard Time (`UTC+05:30`). Phase 1 previously accepted only whole-hour expected local UTC offsets, so the restart initially produced a `LOCAL_CLOCK_DRIFT` row.

Fix applied:

- `InpExpectedLocalUtcOffsetHours` was replaced with `InpExpectedLocalUtcOffsetMinutes`.
- The safe and risk-test presets now use `InpExpectedLocalUtcOffsetMinutes=330`.
- The EA was redeployed and compiled successfully with 0 errors and 0 warnings.
- The latest startup and decision rows report `server_time_status=CLOCK_OK`.

## Weekend Resume Handling

Because the restart happened on Saturday, the latest broker bar is a stale weekend market-break row. The Phase 1 reporting scripts now distinguish this from a runtime failure:

- `verify_phase1_logs.py` tolerates weekend stale-resume gaps in M5 cadence checks.
- `analyze_phase1_soak.py` tolerates weekend stale-resume gaps and historical clock drift when the latest row is `CLOCK_OK`.
- `generate_phase1_runtime_health_report.py` uses the same weekend and latest-clock handling.
- `check_phase1_external_health.py` tolerates stale latest rows during weekend market breaks.

## Latest Verification

- Periodic checks: PASS.
- Log verification: PASS.
- Soak analysis: PASS.
- Runtime health: PASS.
- Would-signal report: PASS.
- Phase 1 acceptance: PENDING.
- Phase 2 readiness: PENDING.

Open gates remain wall-clock or approval dependent:

- Five trading day Phase 1 soak.
- Five observed days for measured spread/cost model.
- Measured-cost revalidation after cost model PASS.
- Phase 1 review index final PASS.
- Project owner approval before Phase 2 paper-mode implementation.
