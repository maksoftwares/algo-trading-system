# A3 Combined Preflight Report

Status: **ATTACHED**

## Boundary

- A3 login: `1033669`.
- Demo only; canonical Phase 2 unchanged.
- A1 (`1025742`) untouched by this work order.
- A2 (`1033030`) untouched.
- Committed defaults remain non-executing; arming is via local terminal presets only.

## Checks

| Check | Status | Evidence |
|---|---|---|
| t4_equivalent_source_tests_both_eas | PASS | Prior A3 source tests passed; committed source unchanged in this work order. |
| mandatory_source_safety_both_eas | PASS | Source/preset checks; local armed presets only changed InpDryRunOnly and InpBrokerActionAllowed. |
| hypotheses_hash_locked_both_eas | PASS | LOCKED_BEFORE_FIRST_TRADE; hypothesis files and hash manifest unchanged. |
| decommission_pass | PASS | WR50/P2WEAKNESS decommission gate. |
| dry_run_session_both_eas_pass | WAIVED_BY_OWNER | Dry-run gate explicitly waived by owner in CODEX_WORK_ORDER_A3_ARM_AND_ATTACH_2026_06_14.md dated 2026-06-14. |
| owner_signature_and_local_preset | RECORDED | Signed work order recorded; local presets Account3RoundRetestGuardedExecutor.armed_owner_20260614.set and Account3RoundRetestStructuredExecutor.armed_owner_20260614.set. |
| ea_t1_ea_t2_attached_to_a3 | PASS | Startup rows show ATTACHED_A3_RDGUARD_V1 and ATTACHED_A3_RDSTRUCT_V1 on account 1033669 with dry_run=false and broker_action_allowed=true. |

## Attach Decision

- Decision: `ATTACHED`
- Monday attach gate: `CLOSED_BY_OWNER_WAIVER_THEN_ATTACHED_TO_A3_DEMO`
- Target account: `1033669`

## Evidence

```json
{
  "latest_guarded_startup": {
    "timestamp_broker": "2026.06.12 20:59:57",
    "timestamp_utc": "2026.06.13 22:31:19",
    "timestamp_local": "2026.06.14 02:31:19",
    "run_id": "A3_RDGUARD_V1_SAFE",
    "account_server": "Capital.ComMena-Demo",
    "account_login": "1033669",
    "symbol": "XAUUSD",
    "magic": "933000",
    "comment": "RDGUARD_V1",
    "allowed_account_logins": "1033669",
    "dry_run": "false",
    "broker_action_allowed": "true",
    "fixed_lot": "0.01",
    "max_open_positions_per_magic": "1",
    "max_estimated_cost_R": "0.1500",
    "cost_warn_R": "0.2000",
    "absolute_reject_cost_R": "0.3000",
    "max_measured_spread_points": "75.00",
    "min_seconds_between_orders": "60",
    "kill_switch_file": "A3_KILL.txt",
    "startup_status": "ATTACHED_A3_RDGUARD_V1"
  },
  "latest_structured_startup": {
    "timestamp_broker": "2026.06.12 20:59:57",
    "timestamp_utc": "2026.06.13 22:31:19",
    "timestamp_local": "2026.06.14 02:31:19",
    "run_id": "A3_RDSTRUCT_V1_SAFE",
    "account_server": "Capital.ComMena-Demo",
    "account_login": "1033669",
    "symbol": "XAUUSD",
    "magic": "933100",
    "comment": "RDSTRUCT_V1",
    "allowed_account_logins": "1033669",
    "dry_run": "false",
    "broker_action_allowed": "true",
    "fixed_lot": "0.01",
    "max_open_positions_per_magic": "1",
    "max_estimated_cost_R": "0.1500",
    "cost_warn_R": "0.2000",
    "absolute_reject_cost_R": "0.3000",
    "max_measured_spread_points": "75.00",
    "min_seconds_between_orders": "60",
    "kill_switch_file": "A3_KILL.txt",
    "startup_status": "ATTACHED_A3_RDSTRUCT_V1"
  },
  "repair_processes": [
    {
      "ProcessId": 12928,
      "ExecutablePath": "C:\\MT5PortableRepairLane\\terminal64.exe",
      "CommandLine": "C:\\MT5PortableRepairLane\\terminal64.exe /portable /config:C:\\MT5PortableRepairLane\\Config\\a3_arm_attach_startup.ini"
    }
  ]
}
```
