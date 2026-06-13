# A3 Dry Run Session Report

Status: **WAIVED_BY_OWNER**

## Boundary

- A3 login: `1033669`.
- Demo only; canonical Phase 2 unchanged.
- A1 (`1025742`) untouched by this work order.
- A2 (`1033030`) untouched.
- Committed defaults remain non-executing; arming is via local terminal presets only.

## Checks

| Check | Status | Evidence |
|---|---|---|
| ea_t1_dry_run_logs_present | WAIVED_BY_OWNER | Owner Ali waived dry-run session in CODEX_WORK_ORDER_A3_ARM_AND_ATTACH_2026_06_14.md dated 2026-06-14; live startup log now C:\MT5PortableRepairLane\MQL5\Files\a3_rdguard_v1_startup.csv. |
| ea_t2_dry_run_logs_present | WAIVED_BY_OWNER | Owner Ali waived dry-run session in CODEX_WORK_ORDER_A3_ARM_AND_ATTACH_2026_06_14.md dated 2026-06-14; live startup log now C:\MT5PortableRepairLane\MQL5\Files\a3_rdstruct_v1_startup.csv. |
| zero_a3_orders_observed | PASS | Pre-attach baseline: local order logs missing and PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv had 0 rows for magics 933000/933100; MT5 read-only query after attach shows 0 target orders/positions. |
| active_session_verified | WAIVED_BY_OWNER | Dry-run active session waived; armed A3 terminal is running from C:\MT5PortableRepairLane\terminal64.exe with startup rows attached at 2026-06-13 22:31:19Z. |

## Evidence

```json
{
  "work_order": "C:\\Users\\ZHAO ZHU INFORMATION\\Downloads\\algo-trading-system\\CODEX_WORK_ORDER_A3_ARM_AND_ATTACH_2026_06_14.md",
  "waiver_owner": "Ali (mohdalikhans97.com@gmail.com)",
  "guarded_startup_log": "C:\\MT5PortableRepairLane\\MQL5\\Files\\a3_rdguard_v1_startup.csv",
  "structured_startup_log": "C:\\MT5PortableRepairLane\\MQL5\\Files\\a3_rdstruct_v1_startup.csv",
  "guarded_signal_log": "C:\\MT5PortableRepairLane\\MQL5\\Files\\a3_rdguard_v1_signal_log.csv",
  "structured_signal_log": "C:\\MT5PortableRepairLane\\MQL5\\Files\\a3_rdstruct_v1_signal_log.csv",
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
  "latest_guarded_signal": {
    "timestamp_broker": "2026.06.12 20:59:57",
    "timestamp_utc": "2026.06.13 22:31:20",
    "timestamp_local": "2026.06.14 02:31:20",
    "run_id": "A3_RDGUARD_V1_SAFE",
    "account_server": "Capital.ComMena-Demo",
    "account_login": "1033669",
    "symbol": "XAUUSD",
    "magic": "933000",
    "comment": "RDGUARD_V1",
    "m5_bar_time": "2026.06.12 20:55:00",
    "bid": "4218.54",
    "ask": "4219.29",
    "spread_points": "75.00",
    "stage": "WAIT_LEVEL_BREAK_RETEST",
    "direction": "LONG",
    "would_signal": "false",
    "reason_code": "no_long_symbol_normalized_round_retest_v0_candidate",
    "guard_reason": "NO_SIGNAL",
    "guard_pass": "false",
    "level_kind": "none",
    "level_price": "0.00",
    "entry_price": "0.00",
    "stop_loss": "0.00",
    "take_profit": "0.00",
    "stop_distance_points": "0.00",
    "ret12_atr": "3.776831",
    "impulse_alignment": "3.776831",
    "estimated_cost_R": "0.0000",
    "cost_warn": "",
    "open_positions_for_magic": "0",
    "streak_sl_count": "0",
    "streak_pause_until": "1970.01.01 00:00:00",
    "daily_realized_pnl_aed": "0.00",
    "daily_pause_until": "1970.01.01 00:00:00",
    "mutex_name": "",
    "confluence_families": "",
    "confluence_count": "0",
    "dry_run": "false",
    "broker_action_allowed": "true"
  },
  "latest_structured_signal": {
    "timestamp_broker": "2026.06.12 20:59:57",
    "timestamp_utc": "2026.06.13 22:31:20",
    "timestamp_local": "2026.06.14 02:31:20",
    "run_id": "A3_RDSTRUCT_V1_SAFE",
    "account_server": "Capital.ComMena-Demo",
    "account_login": "1033669",
    "symbol": "XAUUSD",
    "magic": "933100",
    "comment": "RDSTRUCT_V1",
    "m5_bar_time": "2026.06.12 20:55:00",
    "bid": "4218.54",
    "ask": "4219.29",
    "spread_points": "75.00",
    "stage": "WAIT_LEVEL_BREAK_RETEST",
    "direction": "LONG",
    "would_signal": "false",
    "reason_code": "no_long_symbol_normalized_round_retest_v0_candidate",
    "guard_reason": "NO_SIGNAL",
    "guard_pass": "false",
    "level_kind": "none",
    "level_price": "0.00",
    "entry_price": "0.00",
    "stop_loss": "0.00",
    "take_profit": "0.00",
    "stop_distance_points": "0.00",
    "structure_confirmed": "true",
    "structure_swing_bar_index": "29",
    "structure_swing_time": "2026.06.12 13:30:00",
    "structure_break_direction": "LONG",
    "structure_level": "4209.95",
    "structure_break_close": "4221.53",
    "structure_distance_from_level_points": "1158.00",
    "estimated_cost_R": "0.0000",
    "cost_warn": "",
    "open_positions_for_magic": "0",
    "streak_sl_count": "0",
    "streak_pause_until": "1970.01.01 00:00:00",
    "daily_realized_pnl_aed": "0.00",
    "daily_pause_until": "1970.01.01 00:00:00",
    "mutex_name": "",
    "confluence_families": "",
    "confluence_count": "0",
    "dry_run": "false",
    "broker_action_allowed": "true"
  },
  "mt5_target_orders": [],
  "mt5_target_positions": []
}
```
