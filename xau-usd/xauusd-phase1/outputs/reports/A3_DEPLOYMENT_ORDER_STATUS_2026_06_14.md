# A3 Deployment Order Status - 2026-06-14

Status: **ATTACHED**

## Boundary

- A3 login: `1033669`.
- Demo only; canonical Phase 2 unchanged.
- A1 and A2 untouched.
- Committed defaults remain non-executing; local presets only.

## Attach Timestamp

- UTC: `2026.06.13 22:31:19`
- Dubai local: `2026.06.14 02:31:19`

## Ordered Steps

| Step | Status | Evidence |
|---|---|---|
| compile_ea_t1_ea_t2 | PASS | MetaEditor compile logs report 0 errors, 0 warnings for both EAs. |
| source_tests | PASS | Prior A3 source tests passed; committed source unchanged. |
| hypothesis_lock_manifest | PASS | docs/A3_HYPOTHESIS_HASH_MANIFEST.json unchanged. |
| decommission_gate | PASS | A3_DECOMMISSION_REPORT.md PASS. |
| dry_run_active_session | WAIVED_BY_OWNER | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\CODEX_WORK_ORDER_A3_ARM_AND_ATTACH_2026_06_14.md |
| owner_authorization_local_preset | RECORDED | C:\MT5PortableRepairLane\MQL5\Presets\Account3RoundRetestGuardedExecutor.armed_owner_20260614.set; C:\MT5PortableRepairLane\MQL5\Presets\Account3RoundRetestStructuredExecutor.armed_owner_20260614.set |
| kill_switch_drill | PASS | With A3_KILL.txt present, both EAs wrote SCOPE_LOCK_BLOCK and were removed; final attach occurred only after removing the kill file. |
| attach_ea_t1_ea_t2 | PASS | Startup rows ATTACHED_A3_RDGUARD_V1 / ATTACHED_A3_RDSTRUCT_V1; process C:/MT5PortableRepairLane/terminal64.exe remains running. |
| locked_two_week_window | STARTED | Starts at 2026.06.13 22:31:19 UTC / 2026.06.14 02:31:19 Dubai local. |

## Decision

EA-T1 and EA-T2 are attached to A3 demo account `1033669` using local armed presets.
