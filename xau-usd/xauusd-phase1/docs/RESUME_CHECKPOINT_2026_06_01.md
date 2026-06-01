# Resume Checkpoint - 2026-06-01

## Scope

This checkpoint records the Monday market-open restart after the planned 2026-05-31 shutdown. It is informational and does not authorize Phase 2, paper-mode execution, broker-side execution, or live trading.

## Restart Actions

- Started `C:\MT5PortableGoldMission\terminal64.exe` with `/portable /config:C:\MT5PortableGoldMission\Config\phase1_dry_run_startup.ini`.
- Started `C:\MT5PortableSpreadLogger\terminal64.exe` with `/portable /config:C:\MT5PortableSpreadLogger\Config\phase0_spread_logger_startup.ini`.
- Started the standard MT5 terminal at `C:\Program Files\MetaTrader 5\terminal64.exe` for the existing experimental demo observer profile.
- Confirmed all three `terminal64.exe` processes are running.
- Refreshed Phase 1, Phase 2, Phase 3 experimental, and root `status.html` reports.

## Timezone Correction

The machine is now on Arabian Standard Time (`UTC+04:00`). The deployed Phase 1 safe preset still expected India Standard Time (`UTC+05:30`), so the first two post-restart Phase 1 rows reported `LOCAL_CLOCK_DRIFT`.

Fix applied:

- Updated the deployed `C:\MT5PortableGoldMission\MQL5\Presets\Phase1DryRunShell.safe.set` to `InpExpectedLocalUtcOffsetMinutes=240`.
- Restarted only the Phase 1 dry-run terminal so the preset reloads.
- The passive spread logger stayed running.
- The latest Phase 1 row now reports `server_time_status=CLOCK_OK`.

The two transient `LOCAL_CLOCK_DRIFT` rows are retained in the log as restart evidence. Reports tolerate historical drift when the latest runtime row is back to `CLOCK_OK`.

## Latest Verification

| Area | Status |
| --- | --- |
| Periodic checks | PASS |
| Status dashboard freshness | PASS |
| Status report freshness | PASS |
| Phase 1 acceptance | PENDING |
| Phase 2 readiness | FAIL |
| Phase 1 latest runtime boundary | PASS: `dry_run=true`, `trade_permission=false`, `server_time_status=CLOCK_OK` |
| Phase 1 latest bar | `2026.05.31 23:25:00` broker time |
| Phase 1 decision rows | `1412` |
| Active-market 72-hour streak | PENDING: longest `56.08h / 72h`, current `0.00h` after weekend/open resume |
| Process/code-freeze 96-hour gate | PENDING for the restarted process: process uptime `0.15h / 96h`; code-freeze marker `108.75h / 96h` |
| Five trading day soak | PASS |
| Measured cost model | PENDING: `3 / 5` fresh market days |
| Experimental demo terminal | `DEMO_TERMINAL_VERIFIED_EXPERIMENTAL_OBSERVERS_ATTACHED` |

## Experimental Demo Observer Terminal

The standard MT5 terminal authorized on `Capital.ComMena-Demo`, synchronized with `0 positions` and `0 orders`, and loaded only the expected `Phase2ExperimentalDemoObserver` telemetry charts.

This is still observation-only:

- `broker_action_allowed=false`
- canonical Phase 2 remains unauthorized
- live trading remains unauthorized

## Remaining Objective Gates

- Active-market 72-hour Phase 1 continuity must continue collecting market-open evidence.
- The current restarted Phase 1 process must build fresh uptime evidence. The pre-shutdown 96-hour evidence remains captured in the 2026-05-31 shutdown checkpoint, but current reports now correctly show the post-restart process uptime separately.
- Measured-cost model needs two additional fresh market days.
- Phase 2 VPS selection, latency evidence, first-day verification, and owner approval remain unresolved.

## Boundary

- Phase 1 remains dry-run only.
- Passive spread logging remains observation-only.
- Experimental demo observers remain telemetry-only.
- No broker-side execution or live trading is authorized.
