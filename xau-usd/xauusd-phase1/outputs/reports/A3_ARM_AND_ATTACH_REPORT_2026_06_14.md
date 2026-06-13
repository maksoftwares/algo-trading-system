# A3 Arm And Attach Report - 2026-06-14

Status: **ATTACHED_WITH_GV_SELFTEST_LIMITATION_RECORDED**

## Boundary

- A3 demo login `1033669` only.
- A1 (`1025742`) untouched by this work order.
- A2 (`1033030`) untouched.
- Demo only; no live trading; canonical Phase 2 status unchanged.
- Committed source defaults remain non-executing; arming used local presets under `C:\MT5PortableRepairLane\MQL5\Presets`.
- G1-G6 guard logic, locked parameters, magic bands, and hypothesis/hash manifest were not edited.

## Result

EA-T1 and EA-T2 are attached to A3 via `C:\MT5PortableRepairLane\terminal64.exe` on XAUUSD M5. Latest startup rows show account `1033669`, server `Capital.ComMena-Demo`, `dry_run=false`, and `broker_action_allowed=true` for both EAs. Attached at UTC `2026.06.13 22:31:19` / Dubai local `2026.06.14 02:31:19`.

## GV Self-Test Limitation

The work order requested startup-log confirmation of a GV mutex namespace self-test. The A3 EA sources do not implement `GV_MUTEX_NAMESPACE_SELF_TEST_PASS` or `FAMMUX_SELFTEST` rows. They do implement distinct namespaces `FAMMUX_RD_XAUUSD_...` and `FAMMUX_RDSTRUCT_XAUUSD_...` plus `GlobalVariableSetOnCondition` before `OrderSend`. I did not change source during this attach window; this limitation is recorded here for reviewer follow-up.

## How To Pause

- Create `C:\MT5PortableRepairLane\MQL5\Files\A3_KILL.txt` containing `KILL`; startup and scope locks block new orders while present.
- To stop future broker sends through inputs, set the local preset's `InpBrokerActionAllowed=false` and re-attach/reload the EA charts.
- Existing open positions are unaffected by that flag and must be managed manually if needed.

## Checkout And Git State

```text
COMMAND: git rev-parse --show-toplevel
C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system
COMMAND: git rev-parse HEAD
c8b1f66459ab9bb61d6d43f60ee0e37f4489de41
COMMAND: git status --porcelain
 M status.html
 M xau-usd/xauusd-phase1/outputs/reports/A3_COMBINED_PREFLIGHT_REPORT.json
 M xau-usd/xauusd-phase1/outputs/reports/A3_COMBINED_PREFLIGHT_REPORT.md
 M xau-usd/xauusd-phase1/outputs/reports/A3_DRY_RUN_SESSION_REPORT.json
 M xau-usd/xauusd-phase1/outputs/reports/A3_DRY_RUN_SESSION_REPORT.md
 M xau-usd/xauusd-phase1/outputs/reports/A3_OWNER_AUTHORIZATION_STATUS.json
 M xau-usd/xauusd-phase1/outputs/reports/A3_OWNER_AUTHORIZATION_STATUS.md
 M xau-usd/xauusd-phase1/outputs/reports/PHASE2_DEMO_REPAIR_FORWARD_WEEK_REPORT.json
 M xau-usd/xauusd-phase1/outputs/reports/PHASE2_DEMO_REPAIR_FORWARD_WEEK_REPORT.md
 M xau-usd/xauusd-phase1/outputs/reports/PHASE2_DEMO_REPAIR_MONITOR_LATEST.json
 M xau-usd/xauusd-phase1/outputs/reports/PHASE2_DEMO_REPAIR_MONITOR_LATEST.md
?? CODEX_ADDENDUM_EVENING_SESSION_AND_CONFLUENCE_2026_06_13.md
?? CODEX_WORK_ORDER_A3_ARM_AND_ATTACH_2026_06_14.md
?? CODEX_WORK_ORDER_A3_REPAIR_LANE_2026_06_13.md
?? CODEX_WORK_ORDER_ADDENDUM2_EAT2_EAT3PREP_2026_06_13.md
?? CODEX_WORK_ORDER_T0_T12_REVERIFY_DISCREPANCY_2026_06_14.md
?? DEEP_DIVE_PROFIT_DUPLICATION_AND_CONSENSUS_2026_06_13.md
?? EVENING_SESSION_POSITIVE_GOAL_PLAN_2026_06_13.md
?? PORTFOLIO_AND_FIXED_EA_DEPLOYMENT_PLAN_2026_06_13.md
```

## Local Preset Diffs

```text
COMMAND: git diff --no-index safe guarded vs local armed
diff --git "a/C:\\Users\\ZHAO ZHU INFORMATION\\Downloads\\algo-trading-system\\xau-usd\\xauusd-phase1\\mt5\\Presets\\Account3RoundRetestGuardedExecutor.safe_xauusd.set" "b/C:\\MT5PortableRepairLane\\MQL5\\Presets\\Account3RoundRetestGuardedExecutor.armed_owner_20260614.set"
index 04bb464..198ba21 100644
--- "a/C:\\Users\\ZHAO ZHU INFORMATION\\Downloads\\algo-trading-system\\xau-usd\\xauusd-phase1\\mt5\\Presets\\Account3RoundRetestGuardedExecutor.safe_xauusd.set"	
+++ "b/C:\\MT5PortableRepairLane\\MQL5\\Presets\\Account3RoundRetestGuardedExecutor.armed_owner_20260614.set"
@@ -1,6 +1,6 @@
 InpRunId=A3_RDGUARD_V1_SAFE
-InpDryRunOnly=true
-InpBrokerActionAllowed=false
+InpDryRunOnly=false
+InpBrokerActionAllowed=true
 InpTargetSymbol=XAUUSD
 InpExpectedServerMarker=Demo
 InpAllowedAccountLoginsCsv=1033669
warning: in the working copy of 'C:\MT5PortableRepairLane\MQL5\Presets\Account3RoundRetestGuardedExecutor.armed_owner_20260614.set', CRLF will be replaced by LF the next time Git touches it

COMMAND: git diff --no-index safe structured vs local armed
diff --git "a/C:\\Users\\ZHAO ZHU INFORMATION\\Downloads\\algo-trading-system\\xau-usd\\xauusd-phase1\\mt5\\Presets\\Account3RoundRetestStructuredExecutor.safe_xauusd.set" "b/C:\\MT5PortableRepairLane\\MQL5\\Presets\\Account3RoundRetestStructuredExecutor.armed_owner_20260614.set"
index 3a7b0bd..d47e568 100644
--- "a/C:\\Users\\ZHAO ZHU INFORMATION\\Downloads\\algo-trading-system\\xau-usd\\xauusd-phase1\\mt5\\Presets\\Account3RoundRetestStructuredExecutor.safe_xauusd.set"	
+++ "b/C:\\MT5PortableRepairLane\\MQL5\\Presets\\Account3RoundRetestStructuredExecutor.armed_owner_20260614.set"
@@ -1,6 +1,6 @@
 InpRunId=A3_RDSTRUCT_V1_SAFE
-InpDryRunOnly=true
-InpBrokerActionAllowed=false
+InpDryRunOnly=false
+InpBrokerActionAllowed=true
 InpTargetSymbol=XAUUSD
 InpExpectedServerMarker=Demo
 InpAllowedAccountLoginsCsv=1033669
warning: in the working copy of 'C:\MT5PortableRepairLane\MQL5\Presets\Account3RoundRetestStructuredExecutor.armed_owner_20260614.set', CRLF will be replaced by LF the next time Git touches it
```

## Compile Logs

```text
--- C:\MT5PortableRepairLane\MQL5\Logs\compile_Account3RoundRetestGuardedExecutor.log ---
C:\MT5CompileScratch\A3ArmAttach_20260613_222447\MQL5\Experts\Account3RoundRetestGuardedExecutor.mq5 : information: compiling C:\MT5CompileScratch\A3ArmAttach_20260613_222447\MQL5\Experts\Account3RoundRetestGuardedExecutor.mq5
 : information: generating code
 : information: generating code 3%
 : information: generating code 6%
 : information: generating code 9%
 : information: generating code 12%
 : information: generating code 15%
 : information: generating code 18%
 : information: generating code 21%
 : information: generating code 24%
 : information: generating code 27%
 : information: generating code 30%
 : information: generating code 33%
 : information: generating code 36%
 : information: generating code 39%
 : information: generating code 42%
 : information: generating code 45%
 : information: generating code 48%
 : information: generating code 51%
 : information: generating code 54%
 : information: generating code 57%
 : information: generating code 60%
 : information: generating code 63%
 : information: generating code 66%
 : information: generating code 69%
 : information: generating code 72%
 : information: generating code 75%
 : information: generating code 78%
 : information: generating code 81%
 : information: generating code 84%
 : information: generating code 87%
 : information: generating code 90%
 : information: generating code 93%
 : information: generating code 95%
 : information: generating code 100%
 : information: code generated
Result: 0 errors, 0 warnings, 705 ms elapsed, cpu='X64 Regular'
--- C:\MT5PortableRepairLane\MQL5\Logs\compile_Account3RoundRetestStructuredExecutor.log ---
C:\MT5CompileScratch\A3ArmAttach_20260613_222447\MQL5\Experts\Account3RoundRetestStructuredExecutor.mq5 : information: compiling C:\MT5CompileScratch\A3ArmAttach_20260613_222447\MQL5\Experts\Account3RoundRetestStructuredExecutor.mq5
 : information: generating code
 : information: generating code 3%
 : information: generating code 6%
 : information: generating code 9%
 : information: generating code 12%
 : information: generating code 15%
 : information: generating code 18%
 : information: generating code 21%
 : information: generating code 24%
 : information: generating code 27%
 : information: generating code 30%
 : information: generating code 33%
 : information: generating code 36%
 : information: generating code 39%
 : information: generating code 42%
 : information: generating code 45%
 : information: generating code 48%
 : information: generating code 51%
 : information: generating code 54%
 : information: generating code 57%
 : information: generating code 60%
 : information: generating code 63%
 : information: generating code 66%
 : information: generating code 69%
 : information: generating code 72%
 : information: generating code 75%
 : information: generating code 78%
 : information: generating code 81%
 : information: generating code 84%
 : information: generating code 87%
 : information: generating code 90%
 : information: generating code 93%
 : information: generating code 95%
 : information: generating code 100%
 : information: code generated
Result: 0 errors, 0 warnings, 689 ms elapsed, cpu='X64 Regular'
```

## Kill Drill And Attach Summaries

```text
--- C:\MT5PortableRepairLane\MQL5\Files\a3_arm_attach_summary_20260613_222447.json ---
{
  "created_at_utc": "2026-06-13T22:30:01.143914Z",
  "portable_root": "C:\\MT5PortableRepairLane",
  "terminal_exe": "C:\\MT5PortableRepairLane\\terminal64.exe",
  "startup_config": "C:\\MT5PortableRepairLane\\Config\\a3_arm_attach_startup.ini",
  "profile_backup": "C:\\MT5PortableRepairLane\\_codex_quarantine\\profile_backups\\default_profile_before_a3_arm_attach_20260613_222447",
  "local_presets": {
    "EA-T1": "C:\\MT5PortableRepairLane\\MQL5\\Presets\\Account3RoundRetestGuardedExecutor.armed_owner_20260614.set",
    "EA-T2": "C:\\MT5PortableRepairLane\\MQL5\\Presets\\Account3RoundRetestStructuredExecutor.armed_owner_20260614.set"
  },
  "compile_results": [
    {
      "label": "EA-T1",
      "log": "C:\\MT5PortableRepairLane\\MQL5\\Logs\\compile_Account3RoundRetestGuardedExecutor.log",
      "ex5": "C:\\MT5PortableRepairLane\\MQL5\\Experts\\Account3RoundRetestGuardedExecutor.ex5",
      "ex5_mtime_utc": "2026-06-13T22:24:48.766515Z"
    },
    {
      "label": "EA-T2",
      "log": "C:\\MT5PortableRepairLane\\MQL5\\Logs\\compile_Account3RoundRetestStructuredExecutor.log",
      "ex5": "C:\\MT5PortableRepairLane\\MQL5\\Experts\\Account3RoundRetestStructuredExecutor.ex5",
      "ex5_mtime_utc": "2026-06-13T22:24:50.834054Z"
    }
  ],
  "kill_drill_statuses": {
    "EA-T1": "REMOVED_REASON_8",
    "EA-T2": "REMOVED_REASON_8"
  },
  "final_startup_statuses": {
    "EA-T1": "REMOVED_REASON_8",
    "EA-T2": "REMOVED_REASON_8"
  },
  "signal_counts": {
    "EA-T1": 0,
    "EA-T2": 0
  },
  "startup_logs": {
    "EA-T1": "C:\\MT5PortableRepairLane\\MQL5\\Files\\a3_rdguard_v1_startup.csv",
    "EA-T2": "C:\\MT5PortableRepairLane\\MQL5\\Files\\a3_rdstruct_v1_startup.csv"
  },
  "signal_logs": {
    "EA-T1": "C:\\MT5PortableRepairLane\\MQL5\\Files\\a3_rdguard_v1_signal_log.csv",
    "EA-T2": "C:\\MT5PortableRepairLane\\MQL5\\Files\\a3_rdstruct_v1_signal_log.csv"
  },
  "order_logs": {
    "EA-T1": "C:\\MT5PortableRepairLane\\MQL5\\Files\\a3_rdguard_v1_order_log.csv",
    "EA-T2": "C:\\MT5PortableRepairLane\\MQL5\\Files\\a3_rdstruct_v1_order_log.csv"
  },
  "baseline_broker_csv_magic_counts": {
    "933000": 0,
    "933100": 0
  }
}

--- C:\MT5PortableRepairLane\MQL5\Files\a3_arm_attach_retry_summary_20260613_223111.json ---
{
  "retry_created_at_utc": "2026-06-13T22:31:21.649525Z",
  "closed_before_retry": [
    21796
  ],
  "kill_file_exists_before_final": false,
  "profile_backup": "C:\\MT5PortableRepairLane\\_codex_quarantine\\profile_backups\\default_profile_before_a3_final_attach_retry_20260613_223111",
  "final_startup_statuses": {
    "EA-T1": "ATTACHED_A3_RDGUARD_V1",
    "EA-T2": "ATTACHED_A3_RDSTRUCT_V1"
  },
  "signal_counts": {
    "EA-T1": 1,
    "EA-T2": 1
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

## Startup Logs

```text
--- C:\MT5PortableRepairLane\MQL5\Files\a3_rdguard_v1_startup.csv ---
timestamp_broker,timestamp_utc,timestamp_local,run_id,account_server,account_login,symbol,magic,comment,allowed_account_logins,dry_run,broker_action_allowed,fixed_lot,max_open_positions_per_magic,max_estimated_cost_R,cost_warn_R,absolute_reject_cost_R,max_measured_spread_points,min_seconds_between_orders,kill_switch_file,startup_status
2024.08.23 23:58:59,2026.06.13 22:25:44,2026.06.14 02:25:44,A3_RDGUARD_V1_SAFE,Capital.ComMena-Demo,1033669,XAUUSD,933000,RDGUARD_V1,1033669,false,true,0.01,1,0.1500,0.2000,0.3000,75.00,60,A3_KILL.txt,SCOPE_LOCK_BLOCK
2024.08.23 23:58:59,2026.06.13 22:25:44,2026.06.14 02:25:44,A3_RDGUARD_V1_SAFE,Capital.ComMena-Demo,1033669,XAUUSD,933000,RDGUARD_V1,1033669,false,true,0.01,1,0.1500,0.2000,0.3000,75.00,60,A3_KILL.txt,REMOVED_REASON_8
2026.06.12 20:59:57,2026.06.13 22:25:45,2026.06.14 02:25:45,A3_RDGUARD_V1_SAFE,Capital.ComMena-Demo,1033669,XAUUSD,933000,RDGUARD_V1,1033669,false,true,0.01,1,0.1500,0.2000,0.3000,75.00,60,A3_KILL.txt,SCOPE_LOCK_BLOCK
2026.06.12 20:59:57,2026.06.13 22:25:45,2026.06.14 02:25:45,A3_RDGUARD_V1_SAFE,Capital.ComMena-Demo,1033669,XAUUSD,933000,RDGUARD_V1,1033669,false,true,0.01,1,0.1500,0.2000,0.3000,75.00,60,A3_KILL.txt,REMOVED_REASON_8
2026.06.12 20:59:57,2026.06.13 22:31:19,2026.06.14 02:31:19,A3_RDGUARD_V1_SAFE,Capital.ComMena-Demo,1033669,XAUUSD,933000,RDGUARD_V1,1033669,false,true,0.01,1,0.1500,0.2000,0.3000,75.00,60,A3_KILL.txt,ATTACHED_A3_RDGUARD_V1

--- C:\MT5PortableRepairLane\MQL5\Files\a3_rdstruct_v1_startup.csv ---
timestamp_broker,timestamp_utc,timestamp_local,run_id,account_server,account_login,symbol,magic,comment,allowed_account_logins,dry_run,broker_action_allowed,fixed_lot,max_open_positions_per_magic,max_estimated_cost_R,cost_warn_R,absolute_reject_cost_R,max_measured_spread_points,min_seconds_between_orders,kill_switch_file,startup_status
2024.08.23 23:58:59,2026.06.13 22:25:44,2026.06.14 02:25:44,A3_RDSTRUCT_V1_SAFE,Capital.ComMena-Demo,1033669,XAUUSD,933100,RDSTRUCT_V1,1033669,false,true,0.01,1,0.1500,0.2000,0.3000,75.00,60,A3_KILL.txt,SCOPE_LOCK_BLOCK
2024.08.23 23:58:59,2026.06.13 22:25:44,2026.06.14 02:25:44,A3_RDSTRUCT_V1_SAFE,Capital.ComMena-Demo,1033669,XAUUSD,933100,RDSTRUCT_V1,1033669,false,true,0.01,1,0.1500,0.2000,0.3000,75.00,60,A3_KILL.txt,REMOVED_REASON_8
2026.06.12 20:59:57,2026.06.13 22:25:45,2026.06.14 02:25:45,A3_RDSTRUCT_V1_SAFE,Capital.ComMena-Demo,1033669,XAUUSD,933100,RDSTRUCT_V1,1033669,false,true,0.01,1,0.1500,0.2000,0.3000,75.00,60,A3_KILL.txt,SCOPE_LOCK_BLOCK
2026.06.12 20:59:57,2026.06.13 22:25:45,2026.06.14 02:25:45,A3_RDSTRUCT_V1_SAFE,Capital.ComMena-Demo,1033669,XAUUSD,933100,RDSTRUCT_V1,1033669,false,true,0.01,1,0.1500,0.2000,0.3000,75.00,60,A3_KILL.txt,REMOVED_REASON_8
2026.06.12 20:59:57,2026.06.13 22:31:19,2026.06.14 02:31:19,A3_RDSTRUCT_V1_SAFE,Capital.ComMena-Demo,1033669,XAUUSD,933100,RDSTRUCT_V1,1033669,false,true,0.01,1,0.1500,0.2000,0.3000,75.00,60,A3_KILL.txt,ATTACHED_A3_RDSTRUCT_V1
```

## Signal Logs

```text
--- latest C:\MT5PortableRepairLane\MQL5\Files\a3_rdguard_v1_signal_log.csv ---
{
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
}

--- latest C:\MT5PortableRepairLane\MQL5\Files\a3_rdstruct_v1_signal_log.csv ---
{
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
}
```

## MT5 Read-Only Exposure Query

```text
COMMAND: MetaTrader5 initialize/query A3 portable terminal
{
  "account": {
    "login": 1033669,
    "trade_mode": 0,
    "leverage": 100,
    "limit_orders": 0,
    "margin_so_mode": 0,
    "trade_allowed": true,
    "trade_expert": true,
    "margin_mode": 2,
    "currency_digits": 2,
    "fifo_close": false,
    "balance": 4000.0,
    "credit": 0.0,
    "profit": 0.0,
    "equity": 4000.0,
    "margin": 0.0,
    "margin_free": 4000.0,
    "margin_level": 0.0,
    "margin_so_call": 100.0,
    "margin_so_so": 50.0,
    "margin_initial": 0.0,
    "margin_maintenance": 0.0,
    "assets": 0.0,
    "liabilities": 0.0,
    "commission_blocked": 0.0,
    "name": "MUHAMMAD ALI KHAN",
    "server": "Capital.ComMena-Demo",
    "currency": "AED",
    "company": "Capital Com Mena Securities Trading L.L.C"
  },
  "terminal": {
    "community_account": false,
    "community_connection": false,
    "connected": true,
    "dlls_allowed": false,
    "trade_allowed": true,
    "tradeapi_disabled": false,
    "email_enabled": false,
    "ftp_enabled": false,
    "notifications_enabled": true,
    "mqid": true,
    "build": 5833,
    "maxbars": 100000000,
    "codepage": 0,
    "ping_last": 130829,
    "community_balance": 0.0,
    "retransmission": 0.08493290300662477,
    "company": "MetaQuotes Ltd.",
    "name": "MetaTrader 5",
    "language": "English",
    "path": "C:\\MT5PortableRepairLane",
    "data_path": "C:\\MT5PortableRepairLane",
    "commondata_path": "C:\\Users\\ZHAO ZHU INFORMATION\\AppData\\Roaming\\MetaQuotes\\Terminal\\Common"
  },
  "positions_total": 0,
  "orders_total": 0,
  "target_positions": [],
  "target_orders": []
}
```

## Terminal Process Snapshot

```text
COMMAND: powershell -NoProfile -Command Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'terminal64.exe' -or $_.Name -eq 'MetaEditor64.exe' } | Select-Object ProcessId,Name,ExecutablePath,CommandLine | ConvertTo-Json -Depth 4
[
    {
        "ProcessId":  21248,
        "Name":  "terminal64.exe",
        "ExecutablePath":  "C:\\MT5PortableGoldMission\\terminal64.exe",
        "CommandLine":  "\"C:\\MT5PortableGoldMission\\terminal64.exe\" /portable /config:C:\\MT5PortableGoldMission\\Config\\phase1_dry_run_startup.ini "
    },
    {
        "ProcessId":  16092,
        "Name":  "terminal64.exe",
        "ExecutablePath":  "C:\\MT5PortableSpreadLogger\\terminal64.exe",
        "CommandLine":  "\"C:\\MT5PortableSpreadLogger\\terminal64.exe\" /portable /config:C:\\MT5PortableSpreadLogger\\Config\\phase0_spread_logger_startup.ini "
    },
    {
        "ProcessId":  3144,
        "Name":  "terminal64.exe",
        "ExecutablePath":  "C:\\MT5PortableShadowFixObservers\\terminal64.exe",
        "CommandLine":  "\"C:\\MT5PortableShadowFixObservers\\terminal64.exe\" /portable "
    },
    {
        "ProcessId":  17200,
        "Name":  "terminal64.exe",
        "ExecutablePath":  "C:\\MT5PortableTrendGuardedFixObservers\\terminal64.exe",
        "CommandLine":  "\"C:\\MT5PortableTrendGuardedFixObservers\\terminal64.exe\" /portable "
    },
    {
        "ProcessId":  11724,
        "Name":  "terminal64.exe",
        "ExecutablePath":  "C:\\MT5PortablePositionPathObserver\\terminal64.exe",
        "CommandLine":  "\"C:\\MT5PortablePositionPathObserver\\terminal64.exe\" /portable "
    },
    {
        "ProcessId":  13232,
        "Name":  "terminal64.exe",
        "ExecutablePath":  "C:\\MT5PortableTier1PathObserver\\terminal64.exe",
        "CommandLine":  "C:\\MT5PortableTier1PathObserver\\terminal64.exe /portable /config:C:\\MT5PortableTier1PathObserver\\Config\\position_path_observer_startup.ini"
    },
    {
        "ProcessId":  8780,
        "Name":  "terminal64.exe",
        "ExecutablePath":  "C:\\MT5PortableTier1BestEA\\terminal64.exe",
        "CommandLine":  "\"C:\\MT5PortableTier1BestEA\\terminal64.exe\" /portable /config:C:\\MT5PortableTier1BestEA\\Config\\tier1_bestea_startup.ini "
    },
    {
        "ProcessId":  17676,
        "Name":  "terminal64.exe",
        "ExecutablePath":  "C:\\Program Files\\MetaTrader 5\\terminal64.exe",
        "CommandLine":  "\"C:\\Program Files\\MetaTrader 5\\terminal64.exe\" "
    },
    {
        "ProcessId":  12928,
        "Name":  "terminal64.exe",
        "ExecutablePath":  "C:\\MT5PortableRepairLane\\terminal64.exe",
        "CommandLine":  "C:\\MT5PortableRepairLane\\terminal64.exe /portable /config:C:\\MT5PortableRepairLane\\Config\\a3_arm_attach_startup.ini"
    }
]
```

## Terminal Journal Tail

```text
--- C:\MT5PortableRepairLane\Logs\20260614.log tail ---
LS	0	02:24:54.704	Startup	successfully initialized from start config "C:\MT5PortableRepairLane\Config\a3_arm_attach_startup.ini"
CO	0	02:24:54.735	Terminal	MetaTrader 5 x64 build 5833 started for MetaQuotes Ltd.
JI	0	02:24:54.735	Terminal	Windows 11 build 26200, 16 x 13th Gen Intel Core i7-13620H, AVX2, 18 / 31 Gb memory, 250 / 452 Gb disk, UAC, GMT+4
ME	0	02:24:54.735	Terminal	C:\MT5PortableRepairLane
LL	0	02:24:54.735	Terminal	launched with C:\MT5PortableRepairLane\Config\a3_arm_attach_startup.ini
KI	0	02:24:55.634	Experts	expert Account3RoundRetestGuardedExecutor (XAUUSD,M5) loaded successfully
OE	0	02:24:55.655	Experts	expert Account3RoundRetestStructuredExecutor (XAUUSD,M5) loaded successfully
CI	2	02:25:44.752	Experts	initializing of Account3RoundRetestStructuredExecutor (XAUUSD,M5) failed with code 1
FP	2	02:25:44.754	Experts	initializing of Account3RoundRetestGuardedExecutor (XAUUSD,M5) failed with code 1
RO	0	02:25:44.766	Experts	expert Account3RoundRetestGuardedExecutor (XAUUSD,M5) removed
OM	0	02:25:44.766	Experts	expert Account3RoundRetestStructuredExecutor (XAUUSD,M5) removed
JJ	0	02:25:44.769	Experts	expert Account3RoundRetestStructuredExecutor (XAUUSD,M5) loaded successfully
EF	0	02:25:44.769	Experts	expert Account3RoundRetestGuardedExecutor (XAUUSD,M5) loaded successfully
KQ	0	02:25:45.288	Network	'1033669': authorized on Capital.ComMena-Demo through Access Point 2
JO	0	02:25:45.288	Network	'1033669': previous successful authorization performed from 2.51.167.214 on 2026.06.13 18:36:59
KP	0	02:25:45.673	Network	'1033669': terminal synchronized with Capital Com Mena Securities Trading L.L.C: 0 positions, 0 orders, 232 symbols, 0 spreads
PQ	0	02:25:45.673	Network	'1033669': trading has been enabled - hedging mode
EJ	2	02:25:45.929	Experts	initializing of Account3RoundRetestGuardedExecutor (XAUUSD,M5) failed with code 1
HK	2	02:25:45.930	Experts	initializing of Account3RoundRetestStructuredExecutor (XAUUSD,M5) failed with code 1
GD	0	02:25:45.941	Experts	expert Account3RoundRetestStructuredExecutor (XAUUSD,M5) removed
MN	0	02:25:45.942	Experts	expert Account3RoundRetestGuardedExecutor (XAUUSD,M5) removed
PN	0	02:25:45.973	Network	'1033669': scanning network for access points
PH	0	02:25:47.384	Network	'1033669': scanning network finished
HS	0	02:26:25.082	Terminal	exit with code 0
FQ	0	02:26:25.134	Network	'1033669': disconnected from Capital.ComMena-Demo
CN	0	02:26:25.168	Terminal	stopped with 0
FM	0	02:26:25.171	Terminal	shutdown with 0
GH	0	02:26:30.459	Startup	successfully initialized from start config "C:\MT5PortableRepairLane\Config\a3_arm_attach_startup.ini"
HD	0	02:26:30.479	Terminal	MetaTrader 5 x64 build 5833 started for MetaQuotes Ltd.
GM	0	02:26:30.480	Terminal	Windows 11 build 26200, 16 x 13th Gen Intel Core i7-13620H, AVX2, 18 / 31 Gb memory, 250 / 452 Gb disk, UAC, GMT+4
HN	0	02:26:30.480	Terminal	C:\MT5PortableRepairLane
MI	0	02:26:30.480	Terminal	launched with C:\MT5PortableRepairLane\Config\a3_arm_attach_startup.ini
DJ	0	02:26:31.796	Network	'1033669': authorized on Capital.ComMena-Demo through Access Point 2 (ping: 130.83 ms, build 5800)
ED	0	02:26:31.796	Network	'1033669': previous successful authorization performed from 2.51.167.214 on 2026.06.13 22:25:46
FJ	0	02:26:32.073	Network	'1033669': terminal synchronized with Capital Com Mena Securities Trading L.L.C: 0 positions, 0 orders, 232 symbols, 0 spreads
QH	0	02:26:32.073	Network	'1033669': trading has been enabled - hedging mode
IM	0	02:31:12.308	Terminal	exit with code 0
IK	0	02:31:12.331	Network	'1033669': disconnected from Capital.ComMena-Demo
KP	0	02:31:12.360	Terminal	stopped with 0
CK	0	02:31:12.363	Terminal	shutdown with 0
QR	0	02:31:17.919	Startup	successfully initialized from start config "C:\MT5PortableRepairLane\Config\a3_arm_attach_startup.ini"
DN	0	02:31:17.940	Terminal	MetaTrader 5 x64 build 5833 started for MetaQuotes Ltd.
IG	0	02:31:17.940	Terminal	Windows 11 build 26200, 16 x 13th Gen Intel Core i7-13620H, AVX2, 18 / 31 Gb memory, 250 / 452 Gb disk, UAC, GMT+4
JD	0	02:31:17.940	Terminal	C:\MT5PortableRepairLane
KS	0	02:31:17.940	Terminal	launched with C:\MT5PortableRepairLane\Config\a3_arm_attach_startup.ini
IO	0	02:31:18.837	Experts	expert Account3RoundRetestGuardedExecutor (XAUUSD,M5) loaded successfully
RD	0	02:31:18.857	Experts	expert Account3RoundRetestStructuredExecutor (XAUUSD,M5) loaded successfully
RK	0	02:31:19.330	Network	'1033669': authorized on Capital.ComMena-Demo through Access Point 2 (ping: 130.83 ms, build 5800)
PD	0	02:31:19.330	Network	'1033669': previous successful authorization performed from 2.51.167.214 on 2026.06.13 22:26:33
FI	0	02:31:19.702	Network	'1033669': terminal synchronized with Capital Com Mena Securities Trading L.L.C: 0 positions, 0 orders, 232 symbols, 0 spreads
IH	0	02:31:19.702	Network	'1033669': trading has been enabled - hedging mode
FR	0	02:31:19.718	Trades	use MetaTrader VPS Hosting Service to speed up the execution: 10.74 ms via 'VPS Ireland 01' instead of 130.83 ms
```

## Chart Profile Expert Evidence

```text
COMMAND: powershell -NoProfile -Command Select-String -Path 'C:\MT5PortableRepairLane\MQL5\Profiles\Charts\Default\chart01.chr','C:\MT5PortableRepairLane\MQL5\Profiles\Charts\Default\chart02.chr' -Pattern '<expert>|Account3Round|InpDryRunOnly|InpBrokerActionAllowed|InpAllowedAccountLoginsCsv|path=Experts' | ForEach-Object { "{0}:{1}:{2}" -f $_.Path,$_.LineNumber,$_.Line }
C:\MT5PortableRepairLane\MQL5\Profiles\Charts\Default\chart01.chr:64:<expert>
C:\MT5PortableRepairLane\MQL5\Profiles\Charts\Default\chart01.chr:65:name=Account3RoundRetestGuardedExecutor
C:\MT5PortableRepairLane\MQL5\Profiles\Charts\Default\chart01.chr:66:path=Experts\Account3RoundRetestGuardedExecutor.ex5
C:\MT5PortableRepairLane\MQL5\Profiles\Charts\Default\chart01.chr:70:InpDryRunOnly=false
C:\MT5PortableRepairLane\MQL5\Profiles\Charts\Default\chart01.chr:71:InpBrokerActionAllowed=true
C:\MT5PortableRepairLane\MQL5\Profiles\Charts\Default\chart01.chr:74:InpAllowedAccountLoginsCsv=1033669
C:\MT5PortableRepairLane\MQL5\Profiles\Charts\Default\chart02.chr:64:<expert>
C:\MT5PortableRepairLane\MQL5\Profiles\Charts\Default\chart02.chr:65:name=Account3RoundRetestStructuredExecutor
C:\MT5PortableRepairLane\MQL5\Profiles\Charts\Default\chart02.chr:66:path=Experts\Account3RoundRetestStructuredExecutor.ex5
C:\MT5PortableRepairLane\MQL5\Profiles\Charts\Default\chart02.chr:70:InpDryRunOnly=false
C:\MT5PortableRepairLane\MQL5\Profiles\Charts\Default\chart02.chr:71:InpBrokerActionAllowed=true
C:\MT5PortableRepairLane\MQL5\Profiles\Charts\Default\chart02.chr:74:InpAllowedAccountLoginsCsv=1033669
```

## Source/Hypothesis Diff Guard

```text
COMMAND: git diff --name-only -- xau-usd/xauusd-phase1/mt5 xau-usd/xauusd-phase1/docs/A3_HYPOTHESIS_HASH_MANIFEST.json xau-usd/xauusd-phase1/docs/A3_ROUND_RETEST_GUARDED_HYPOTHESIS_2026_06_13.md xau-usd/xauusd-phase1/docs/A3_ROUND_RETEST_STRUCTURED_HYPOTHESIS_2026_06_13.md
```

## GV Namespace Source Evidence

```text
COMMAND: rg -n SELF_TEST|GV_MUTEX_NAMESPACE|FAMMUX_SELFTEST|FAMMUX_RD|FAMMUX_RDSTRUCT|GlobalVariableSetOnCondition xau-usd/xauusd-phase1/mt5/Experts/Account3RoundRetestGuardedExecutor.mq5 xau-usd/xauusd-phase1/mt5/Experts/Account3RoundRetestStructuredExecutor.mq5
xau-usd/xauusd-phase1/mt5/Experts/Account3RoundRetestGuardedExecutor.mq5:821:   return "FAMMUX_RD_XAUUSD_" + direction + "_" + CompactDateTimeForGlobalVariable(bar_time);
xau-usd/xauusd-phase1/mt5/Experts/Account3RoundRetestGuardedExecutor.mq5:875:   if(GlobalVariableSetOnCondition(mutex_name, InpMagicNumber, 0))
xau-usd/xauusd-phase1/mt5/Experts/Account3RoundRetestStructuredExecutor.mq5:912:   return "FAMMUX_RDSTRUCT_XAUUSD_" + direction + "_" + CompactDateTimeForGlobalVariable(bar_time);
xau-usd/xauusd-phase1/mt5/Experts/Account3RoundRetestStructuredExecutor.mq5:966:   if(GlobalVariableSetOnCondition(mutex_name, InpMagicNumber, 0))
```

## Report Trail Diff

```text
COMMAND: git diff -- xau-usd/xauusd-phase1/outputs/reports/A3_DRY_RUN_SESSION_REPORT.md xau-usd/xauusd-phase1/outputs/reports/A3_OWNER_AUTHORIZATION_STATUS.md xau-usd/xauusd-phase1/outputs/reports/A3_COMBINED_PREFLIGHT_REPORT.md xau-usd/xauusd-phase1/outputs/reports/A3_DEPLOYMENT_ORDER_STATUS_2026_06_14.md
diff --git a/xau-usd/xauusd-phase1/outputs/reports/A3_COMBINED_PREFLIGHT_REPORT.md b/xau-usd/xauusd-phase1/outputs/reports/A3_COMBINED_PREFLIGHT_REPORT.md
index 2cf8442..493f12d 100644
--- a/xau-usd/xauusd-phase1/outputs/reports/A3_COMBINED_PREFLIGHT_REPORT.md
+++ b/xau-usd/xauusd-phase1/outputs/reports/A3_COMBINED_PREFLIGHT_REPORT.md
@@ -1,27 +1,89 @@
 # A3 Combined Preflight Report
 
-Status: **PENDING**
+Status: **ATTACHED**
 
 ## Boundary
 
 - A3 login: `1033669`.
 - Demo only; canonical Phase 2 unchanged.
-- A2 remains untouched.
-- Committed defaults remain non-executing.
+- A1 (`1025742`) untouched by this work order.
+- A2 (`1033030`) untouched.
+- Committed defaults remain non-executing; arming is via local terminal presets only.
 
 ## Checks
 
 | Check | Status | Evidence |
 |---|---|---|
-| t4_equivalent_source_tests_both_eas | PASS | ============================= 22 passed in 0.12s ============================== |
-| mandatory_source_safety_both_eas | PASS | source/preset checks |
-| hypotheses_hash_locked_both_eas | PASS | LOCKED_BEFORE_FIRST_TRADE |
+| t4_equivalent_source_tests_both_eas | PASS | Prior A3 source tests passed; committed source unchanged in this work order. |
+| mandatory_source_safety_both_eas | PASS | Source/preset checks; local armed presets only changed InpDryRunOnly and InpBrokerActionAllowed. |
+| hypotheses_hash_locked_both_eas | PASS | LOCKED_BEFORE_FIRST_TRADE; hypothesis files and hash manifest unchanged. |
 | decommission_pass | PASS | WR50/P2WEAKNESS decommission gate. |
-| dry_run_session_both_eas_pass | PENDING | Both EAs require dry-run logs before arming. |
-| owner_signature_and_local_preset | PENDING | Owner must sign and supply local execution preset. |
+| dry_run_session_both_eas_pass | WAIVED_BY_OWNER | Dry-run gate explicitly waived by owner in CODEX_WORK_ORDER_A3_ARM_AND_ATTACH_2026_06_14.md dated 2026-06-14. |
+| owner_signature_and_local_preset | RECORDED | Signed work order recorded; local presets Account3RoundRetestGuardedExecutor.armed_owner_20260614.set and Account3RoundRetestStructuredExecutor.armed_owner_20260614.set. |
+| ea_t1_ea_t2_attached_to_a3 | PASS | Startup rows show ATTACHED_A3_RDGUARD_V1 and ATTACHED_A3_RDSTRUCT_V1 on account 1033669 with dry_run=false and broker_action_allowed=true. |
 
 ## Attach Decision
 
-- Decision: `DO_NOT_ATTACH`
-- Monday attach gate: `CLOSED_UNTIL_ALL_CHECKS_PASS`
+- Decision: `ATTACHED`
+- Monday attach gate: `CLOSED_BY_OWNER_WAIVER_THEN_ATTACHED_TO_A3_DEMO`
 - Target account: `1033669`
+
+## Evidence
+
+```json
+{
+  "latest_guarded_startup": {
+    "timestamp_broker": "2026.06.12 20:59:57",
+    "timestamp_utc": "2026.06.13 22:31:19",
+    "timestamp_local": "2026.06.14 02:31:19",
+    "run_id": "A3_RDGUARD_V1_SAFE",
+    "account_server": "Capital.ComMena-Demo",
+    "account_login": "1033669",
+    "symbol": "XAUUSD",
+    "magic": "933000",
+    "comment": "RDGUARD_V1",
+    "allowed_account_logins": "1033669",
+    "dry_run": "false",
+    "broker_action_allowed": "true",
+    "fixed_lot": "0.01",
+    "max_open_positions_per_magic": "1",
+    "max_estimated_cost_R": "0.1500",
+    "cost_warn_R": "0.2000",
+    "absolute_reject_cost_R": "0.3000",
+    "max_measured_spread_points": "75.00",
+    "min_seconds_between_orders": "60",
+    "kill_switch_file": "A3_KILL.txt",
+    "startup_status": "ATTACHED_A3_RDGUARD_V1"
+  },
+  "latest_structured_startup": {
+    "timestamp_broker": "2026.06.12 20:59:57",
+    "timestamp_utc": "2026.06.13 22:31:19",
+    "timestamp_local": "2026.06.14 02:31:19",
+    "run_id": "A3_RDSTRUCT_V1_SAFE",
+    "account_server": "Capital.ComMena-Demo",
+    "account_login": "1033669",
+    "symbol": "XAUUSD",
+    "magic": "933100",
+    "comment": "RDSTRUCT_V1",
+    "allowed_account_logins": "1033669",
+    "dry_run": "false",
+    "broker_action_allowed": "true",
+    "fixed_lot": "0.01",
+    "max_open_positions_per_magic": "1",
+    "max_estimated_cost_R": "0.1500",
+    "cost_warn_R": "0.2000",
+    "absolute_reject_cost_R": "0.3000",
+    "max_measured_spread_points": "75.00",
+    "min_seconds_between_orders": "60",
+    "kill_switch_file": "A3_KILL.txt",
+    "startup_status": "ATTACHED_A3_RDSTRUCT_V1"
+  },
+  "repair_processes": [
+    {
+      "ProcessId": 12928,
+      "ExecutablePath": "C:\\MT5PortableRepairLane\\terminal64.exe",
+      "CommandLine": "C:\\MT5PortableRepairLane\\terminal64.exe /portable /config:C:\\MT5PortableRepairLane\\Config\\a3_arm_attach_startup.ini"
+    }
+  ]
+}
+```
diff --git a/xau-usd/xauusd-phase1/outputs/reports/A3_DRY_RUN_SESSION_REPORT.md b/xau-usd/xauusd-phase1/outputs/reports/A3_DRY_RUN_SESSION_REPORT.md
index 0ec2b5f..d2d81b7 100644
--- a/xau-usd/xauusd-phase1/outputs/reports/A3_DRY_RUN_SESSION_REPORT.md
+++ b/xau-usd/xauusd-phase1/outputs/reports/A3_DRY_RUN_SESSION_REPORT.md
@@ -1,30 +1,168 @@
 # A3 Dry Run Session Report
 
-Status: **PENDING**
+Status: **WAIVED_BY_OWNER**
 
 ## Boundary
 
 - A3 login: `1033669`.
 - Demo only; canonical Phase 2 unchanged.
-- A2 remains untouched.
-- Committed defaults remain non-executing.
+- A1 (`1025742`) untouched by this work order.
+- A2 (`1033030`) untouched.
+- Committed defaults remain non-executing; arming is via local terminal presets only.
 
 ## Checks
 
 | Check | Status | Evidence |
 |---|---|---|
-| ea_t1_dry_run_logs_present | PENDING | logs=[] |
-| ea_t2_dry_run_logs_present | PENDING | logs=[] |
-| zero_a3_orders_observed | PASS | No A3 order logs or broker rows with magics 933000/933100 observed. |
-| active_session_verified | PENDING | A3 terminal was prepared but not launched; owner login credentials/signature still required. |
+| ea_t1_dry_run_logs_present | WAIVED_BY_OWNER | Owner Ali waived dry-run session in CODEX_WORK_ORDER_A3_ARM_AND_ATTACH_2026_06_14.md dated 2026-06-14; live startup log now C:\MT5PortableRepairLane\MQL5\Files\a3_rdguard_v1_startup.csv. |
+| ea_t2_dry_run_logs_present | WAIVED_BY_OWNER | Owner Ali waived dry-run session in CODEX_WORK_ORDER_A3_ARM_AND_ATTACH_2026_06_14.md dated 2026-06-14; live startup log now C:\MT5PortableRepairLane\MQL5\Files\a3_rdstruct_v1_startup.csv. |
+| zero_a3_orders_observed | PASS | Pre-attach baseline: local order logs missing and PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv had 0 rows for magics 933000/933100; MT5 read-only query after attach shows 0 target orders/positions. |
+| active_session_verified | WAIVED_BY_OWNER | Dry-run active session waived; armed A3 terminal is running from C:\MT5PortableRepairLane\terminal64.exe with startup rows attached at 2026-06-13 22:31:19Z. |
 
 ## Evidence
 
 ```json
 {
-  "guarded_signal_logs": [],
-  "structured_signal_logs": [],
-  "guarded_startup_logs": [],
-  "structured_startup_logs": []
+  "work_order": "C:\\Users\\ZHAO ZHU INFORMATION\\Downloads\\algo-trading-system\\CODEX_WORK_ORDER_A3_ARM_AND_ATTACH_2026_06_14.md",
+  "waiver_owner": "Ali (mohdalikhans97.com@gmail.com)",
+  "guarded_startup_log": "C:\\MT5PortableRepairLane\\MQL5\\Files\\a3_rdguard_v1_startup.csv",
+  "structured_startup_log": "C:\\MT5PortableRepairLane\\MQL5\\Files\\a3_rdstruct_v1_startup.csv",
+  "guarded_signal_log": "C:\\MT5PortableRepairLane\\MQL5\\Files\\a3_rdguard_v1_signal_log.csv",
+  "structured_signal_log": "C:\\MT5PortableRepairLane\\MQL5\\Files\\a3_rdstruct_v1_signal_log.csv",
+  "latest_guarded_startup": {
+    "timestamp_broker": "2026.06.12 20:59:57",
+    "timestamp_utc": "2026.06.13 22:31:19",
+    "timestamp_local": "2026.06.14 02:31:19",
+    "run_id": "A3_RDGUARD_V1_SAFE",
+    "account_server": "Capital.ComMena-Demo",
+    "account_login": "1033669",
+    "symbol": "XAUUSD",
+    "magic": "933000",
+    "comment": "RDGUARD_V1",
+    "allowed_account_logins": "1033669",
+    "dry_run": "false",
+    "broker_action_allowed": "true",
+    "fixed_lot": "0.01",
+    "max_open_positions_per_magic": "1",
+    "max_estimated_cost_R": "0.1500",
+    "cost_warn_R": "0.2000",
+    "absolute_reject_cost_R": "0.3000",
+    "max_measured_spread_points": "75.00",
+    "min_seconds_between_orders": "60",
+    "kill_switch_file": "A3_KILL.txt",
+    "startup_status": "ATTACHED_A3_RDGUARD_V1"
+  },
+  "latest_structured_startup": {
+    "timestamp_broker": "2026.06.12 20:59:57",
+    "timestamp_utc": "2026.06.13 22:31:19",
+    "timestamp_local": "2026.06.14 02:31:19",
+    "run_id": "A3_RDSTRUCT_V1_SAFE",
+    "account_server": "Capital.ComMena-Demo",
+    "account_login": "1033669",
+    "symbol": "XAUUSD",
+    "magic": "933100",
+    "comment": "RDSTRUCT_V1",
+    "allowed_account_logins": "1033669",
+    "dry_run": "false",
+    "broker_action_allowed": "true",
+    "fixed_lot": "0.01",
+    "max_open_positions_per_magic": "1",
+    "max_estimated_cost_R": "0.1500",
+    "cost_warn_R": "0.2000",
+    "absolute_reject_cost_R": "0.3000",
+    "max_measured_spread_points": "75.00",
+    "min_seconds_between_orders": "60",
+    "kill_switch_file": "A3_KILL.txt",
+    "startup_status": "ATTACHED_A3_RDSTRUCT_V1"
+  },
+  "latest_guarded_signal": {
+    "timestamp_broker": "2026.06.12 20:59:57",
+    "timestamp_utc": "2026.06.13 22:31:20",
+    "timestamp_local": "2026.06.14 02:31:20",
+    "run_id": "A3_RDGUARD_V1_SAFE",
+    "account_server": "Capital.ComMena-Demo",
+    "account_login": "1033669",
+    "symbol": "XAUUSD",
+    "magic": "933000",
+    "comment": "RDGUARD_V1",
+    "m5_bar_time": "2026.06.12 20:55:00",
+    "bid": "4218.54",
+    "ask": "4219.29",
+    "spread_points": "75.00",
+    "stage": "WAIT_LEVEL_BREAK_RETEST",
+    "direction": "LONG",
+    "would_signal": "false",
+    "reason_code": "no_long_symbol_normalized_round_retest_v0_candidate",
+    "guard_reason": "NO_SIGNAL",
+    "guard_pass": "false",
+    "level_kind": "none",
+    "level_price": "0.00",
+    "entry_price": "0.00",
+    "stop_loss": "0.00",
+    "take_profit": "0.00",
+    "stop_distance_points": "0.00",
+    "ret12_atr": "3.776831",
+    "impulse_alignment": "3.776831",
+    "estimated_cost_R": "0.0000",
+    "cost_warn": "",
+    "open_positions_for_magic": "0",
+    "streak_sl_count": "0",
+    "streak_pause_until": "1970.01.01 00:00:00",
+    "daily_realized_pnl_aed": "0.00",
+    "daily_pause_until": "1970.01.01 00:00:00",
+    "mutex_name": "",
+    "confluence_families": "",
+    "confluence_count": "0",
+    "dry_run": "false",
+    "broker_action_allowed": "true"
+  },
+  "latest_structured_signal": {
+    "timestamp_broker": "2026.06.12 20:59:57",
+    "timestamp_utc": "2026.06.13 22:31:20",
+    "timestamp_local": "2026.06.14 02:31:20",
+    "run_id": "A3_RDSTRUCT_V1_SAFE",
+    "account_server": "Capital.ComMena-Demo",
+    "account_login": "1033669",
+    "symbol": "XAUUSD",
+    "magic": "933100",
+    "comment": "RDSTRUCT_V1",
+    "m5_bar_time": "2026.06.12 20:55:00",
+    "bid": "4218.54",
+    "ask": "4219.29",
+    "spread_points": "75.00",
+    "stage": "WAIT_LEVEL_BREAK_RETEST",
+    "direction": "LONG",
+    "would_signal": "false",
+    "reason_code": "no_long_symbol_normalized_round_retest_v0_candidate",
+    "guard_reason": "NO_SIGNAL",
+    "guard_pass": "false",
+    "level_kind": "none",
+    "level_price": "0.00",
+    "entry_price": "0.00",
+    "stop_loss": "0.00",
+    "take_profit": "0.00",
+    "stop_distance_points": "0.00",
+    "structure_confirmed": "true",
+    "structure_swing_bar_index": "29",
+    "structure_swing_time": "2026.06.12 13:30:00",
+    "structure_break_direction": "LONG",
+    "structure_level": "4209.95",
+    "structure_break_close": "4221.53",
+    "structure_distance_from_level_points": "1158.00",
+    "estimated_cost_R": "0.0000",
+    "cost_warn": "",
+    "open_positions_for_magic": "0",
+    "streak_sl_count": "0",
+    "streak_pause_until": "1970.01.01 00:00:00",
+    "daily_realized_pnl_aed": "0.00",
+    "daily_pause_until": "1970.01.01 00:00:00",
+    "mutex_name": "",
+    "confluence_families": "",
+    "confluence_count": "0",
+    "dry_run": "false",
+    "broker_action_allowed": "true"
+  },
+  "mt5_target_orders": [],
+  "mt5_target_positions": []
 }
 ```
diff --git a/xau-usd/xauusd-phase1/outputs/reports/A3_OWNER_AUTHORIZATION_STATUS.md b/xau-usd/xauusd-phase1/outputs/reports/A3_OWNER_AUTHORIZATION_STATUS.md
index 0c81a2d..4f5407c 100644
--- a/xau-usd/xauusd-phase1/outputs/reports/A3_OWNER_AUTHORIZATION_STATUS.md
+++ b/xau-usd/xauusd-phase1/outputs/reports/A3_OWNER_AUTHORIZATION_STATUS.md
@@ -1,18 +1,32 @@
 # A3 Owner Authorization Status
 
-Status: **PENDING**
+Status: **RECORDED**
 
 ## Boundary
 
 - A3 login: `1033669`.
 - Demo only; canonical Phase 2 unchanged.
-- A2 remains untouched.
-- Committed defaults remain non-executing.
+- A1 (`1025742`) untouched by this work order.
+- A2 (`1033030`) untouched.
+- Committed defaults remain non-executing; arming is via local terminal presets only.
 
 ## Checks
 
 | Check | Status | Evidence |
 |---|---|---|
 | owner_packet_template_exists | PASS | template file |
-| owner_signature_recorded | PENDING | No signed owner packet found in repo-local evidence. |
-| owner_execution_preset_local_only | PENDING | No local owner execution preset was supplied to Codex; committed presets remain safe. |
+| owner_signature_recorded | RECORDED | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\CODEX_WORK_ORDER_A3_ARM_AND_ATTACH_2026_06_14.md |
+| owner_execution_preset_local_only | RECORDED | C:\MT5PortableRepairLane\MQL5\Presets\Account3RoundRetestGuardedExecutor.armed_owner_20260614.set; C:\MT5PortableRepairLane\MQL5\Presets\Account3RoundRetestStructuredExecutor.armed_owner_20260614.set |
+
+## Evidence
+
+```json
+{
+  "work_order": "C:\\Users\\ZHAO ZHU INFORMATION\\Downloads\\algo-trading-system\\CODEX_WORK_ORDER_A3_ARM_AND_ATTACH_2026_06_14.md",
+  "local_presets": {
+    "EA-T1": "C:\\MT5PortableRepairLane\\MQL5\\Presets\\Account3RoundRetestGuardedExecutor.armed_owner_20260614.set",
+    "EA-T2": "C:\\MT5PortableRepairLane\\MQL5\\Presets\\Account3RoundRetestStructuredExecutor.armed_owner_20260614.set"
+  },
+  "preset_scope": "local-only under C:/MT5PortableRepairLane/MQL5/Presets; not committed canonical defaults"
+}
+```
warning: in the working copy of 'xau-usd/xauusd-phase1/outputs/reports/A3_COMBINED_PREFLIGHT_REPORT.md', CRLF will be replaced by LF the next time Git touches it
warning: in the working copy of 'xau-usd/xauusd-phase1/outputs/reports/A3_DRY_RUN_SESSION_REPORT.md', CRLF will be replaced by LF the next time Git touches it
warning: in the working copy of 'xau-usd/xauusd-phase1/outputs/reports/A3_OWNER_AUTHORIZATION_STATUS.md', CRLF will be replaced by LF the next time Git touches it
```
