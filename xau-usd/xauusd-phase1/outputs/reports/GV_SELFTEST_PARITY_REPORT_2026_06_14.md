# GV Self-Test Parity Report - 2026-06-14

Status: **PASS - ATTACHED**

## Boundary

- A3 demo login `1033669` only.
- A1 (`1025742`) and A2 (`1033030`) terminals/processes were not restarted or edited.
- Demo only; no live trading change; canonical Phase 2 status unchanged.
- G1-G6 guard logic, hypothesis parameters, magic numbers/bands, EA-T3 reservation, and `A3_HYPOTHESIS_HASH_MANIFEST.json` were not changed.
- Committed defaults remain non-executing: `InpDryRunOnly=true`, `InpBrokerActionAllowed=false`; the running A3 attach uses the existing local armed presets only.

## Result

EA-T1 and EA-T2 now mirror A1's GV mutex namespace startup self-test pattern. Both EAs compiled cleanly, the A3 pytest set passed, and both reattached to A3 with the expected startup order:

1. `GV_MUTEX_NAMESPACE_SELF_TEST_PASS ...`
2. `ATTACHED_A3_RDGUARD_V1` / `ATTACHED_A3_RDSTRUCT_V1`

Detach timestamp: UTC `2026.06.13 22:57:06`, Dubai local `2026.06.14 02:57:06`.
Reattach timestamp: UTC `2026.06.13 23:02:29`, Dubai local `2026.06.14 03:02:29`.

## How To Pause

- Create `C:\MT5PortableRepairLane\MQL5\Files\A3_KILL.txt` containing `KILL`; startup and scope locks block new orders while present.
- To stop future broker sends through inputs, set the local preset's `InpBrokerActionAllowed=false` and re-attach/reload the EA charts.
- Existing open positions are unaffected by that flag and must be managed manually if needed.

## Source Diff

```diff
diff --git a/xau-usd/xauusd-phase1/mt5/Experts/Account3RoundRetestGuardedExecutor.mq5 b/xau-usd/xauusd-phase1/mt5/Experts/Account3RoundRetestGuardedExecutor.mq5
index 6a69122..158fd77 100644
--- a/xau-usd/xauusd-phase1/mt5/Experts/Account3RoundRetestGuardedExecutor.mq5
+++ b/xau-usd/xauusd-phase1/mt5/Experts/Account3RoundRetestGuardedExecutor.mq5
@@ -881,6 +881,33 @@ bool ClaimMutexBeforeOrder(const A3RoundRetestObservation &observation, string &
   return false;
}

+bool RunFamilyMutexNamespaceSelfTest(string &status_text)
+{
+   string test_name = "FAMMUX_SELFTEST_RD_" + IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN)) + "_" + CompactDateTimeForGlobalVariable(TimeGMT());
+   if(GlobalVariableCheck(test_name))
+      GlobalVariableDel(test_name);
+   bool created = EnsureMutexSlot(test_name);
+   bool claimed = false;
+   bool deleted = false;
+   double stored_value = 0.0;
+   if(created)
+   {
+      ResetLastError();
+      claimed = GlobalVariableSetOnCondition(test_name, (double)InpMagicNumber, 0.0);
+      if(GlobalVariableCheck(test_name))
+         stored_value = GlobalVariableGet(test_name);
+      deleted = GlobalVariableDel(test_name);
+   }
+   bool passed = created && claimed && ((int)stored_value == InpMagicNumber) && deleted;
+   status_text = passed
+      ? "GV_MUTEX_NAMESPACE_SELF_TEST_PASS name=" + test_name
+      : "GV_MUTEX_NAMESPACE_SELF_TEST_FAIL name=" + test_name
+         + " created=" + BoolText(created)
+         + " claimed=" + BoolText(claimed)
+         + " deleted=" + BoolText(deleted);
+   return passed;
+}
+
 bool TradingGuardsPass(
    const A3RoundRetestObservation &observation,
    const double spread_points,
@@ -1140,6 +1167,13 @@ int OnInit()
       WriteStartupRow("SCOPE_LOCK_BLOCK");
       return INIT_FAILED;
    }
+   string gv_mutex_self_test_status = "";
+   if(!RunFamilyMutexNamespaceSelfTest(gv_mutex_self_test_status))
+   {
+      WriteStartupRow(gv_mutex_self_test_status);
+      return INIT_FAILED;
+   }
+   WriteStartupRow(gv_mutex_self_test_status);
    WriteStartupRow("ATTACHED_A3_RDGUARD_V1");
    EventSetTimer(1);
    return INIT_SUCCEEDED;
diff --git a/xau-usd/xauusd-phase1/mt5/Experts/Account3RoundRetestStructuredExecutor.mq5 b/xau-usd/xauusd-phase1/mt5/Experts/Account3RoundRetestStructuredExecutor.mq5
index 8b9218c..ebacedd 100644
--- a/xau-usd/xauusd-phase1/mt5/Experts/Account3RoundRetestStructuredExecutor.mq5
+++ b/xau-usd/xauusd-phase1/mt5/Experts/Account3RoundRetestStructuredExecutor.mq5
@@ -972,6 +972,33 @@ bool ClaimMutexBeforeOrder(const A3RoundRetestObservation &observation, string &
   return false;
}

+bool RunFamilyMutexNamespaceSelfTest(string &status_text)
+{
+   string test_name = "FAMMUX_SELFTEST_RDSTRUCT_" + IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN)) + "_" + CompactDateTimeForGlobalVariable(TimeGMT());
+   if(GlobalVariableCheck(test_name))
+      GlobalVariableDel(test_name);
+   bool created = EnsureMutexSlot(test_name);
+   bool claimed = false;
+   bool deleted = false;
+   double stored_value = 0.0;
+   if(created)
+   {
+      ResetLastError();
+      claimed = GlobalVariableSetOnCondition(test_name, (double)InpMagicNumber, 0.0);
+      if(GlobalVariableCheck(test_name))
+         stored_value = GlobalVariableGet(test_name);
+      deleted = GlobalVariableDel(test_name);
+   }
+   bool passed = created && claimed && ((int)stored_value == InpMagicNumber) && deleted;
+   status_text = passed
+      ? "GV_MUTEX_NAMESPACE_SELF_TEST_PASS name=" + test_name
+      : "GV_MUTEX_NAMESPACE_SELF_TEST_FAIL name=" + test_name
+         + " created=" + BoolText(created)
+         + " claimed=" + BoolText(claimed)
+         + " deleted=" + BoolText(deleted);
+   return passed;
+}
+
 bool TradingGuardsPass(
    const A3RoundRetestObservation &observation,
    const A3StructureState &structure_state,
@@ -1235,6 +1262,13 @@ int OnInit()
       WriteStartupRow("SCOPE_LOCK_BLOCK");
       return INIT_FAILED;
    }
+   string gv_mutex_self_test_status = "";
+   if(!RunFamilyMutexNamespaceSelfTest(gv_mutex_self_test_status))
+   {
+      WriteStartupRow(gv_mutex_self_test_status);
+      return INIT_FAILED;
+   }
+   WriteStartupRow(gv_mutex_self_test_status);
    WriteStartupRow("ATTACHED_A3_RDSTRUCT_V1");
    EventSetTimer(1);
    return INIT_SUCCEEDED;
```

## Test Guard Diff

```diff
diff --git a/xau-usd/xauusd-phase1/tests/test_a3_executors_source.py b/xau-usd/xauusd-phase1/tests/test_a3_executors_source.py
index d42976a..d843c2b 100644
--- a/xau-usd/xauusd-phase1/tests/test_a3_executors_source.py
+++ b/xau-usd/xauusd-phase1/tests/test_a3_executors_source.py
@@ -132,6 +132,25 @@ def test_a3_gv_mutex_claim_occurs_before_order_send():
         assert "GlobalVariableSetOnCondition" in text


+def test_a3_executors_write_startup_gv_mutex_self_test_rows():
+    cases = (
+        (EA_T1, "FAMMUX_SELFTEST_RD_", "ATTACHED_A3_RDGUARD_V1"),
+        (EA_T2, "FAMMUX_SELFTEST_RDSTRUCT_", "ATTACHED_A3_RDSTRUCT_V1"),
+    )
+    for path, prefix, attached_status in cases:
+        text = _text(path)
+        self_test_call = text.index("RunFamilyMutexNamespaceSelfTest(gv_mutex_self_test_status)")
+        attached_row = text.index(f'WriteStartupRow("{attached_status}")')
+
+        assert self_test_call < attached_row
+        assert "RunFamilyMutexNamespaceSelfTest" in text
+        assert prefix in text
+        assert "GV_MUTEX_NAMESPACE_SELF_TEST_PASS" in text
+        assert "GV_MUTEX_NAMESPACE_SELF_TEST_FAIL" in text
+        assert "WriteStartupRow(gv_mutex_self_test_status);" in text
+        assert "GlobalVariableSetOnCondition(test_name, (double)InpMagicNumber, 0.0)" in text
+
+
 def test_a3_eas_have_no_position_management_or_order_deletion_calls():
     for path in (EA_T1, EA_T2):
         text = _text(path)
```

## Pytest Output

COMMAND:

```text
& "xau-usd/xauusd-phase0/.venv/Scripts/python.exe" -m pytest "xau-usd/xauusd-phase1/tests/test_a3_executors_source.py" "xau-usd/xauusd-phase1/tests/test_a3_executor_presets.py" "xau-usd/xauusd-phase1/tests/test_a3_review_reports.py" "xau-usd/xauusd-phase1/tests/test_a3_runtime_reports.py" "xau-usd/xauusd-phase1/tests/test_phase2_experimental_demo_mutex.py" -v
```

OUTPUT:

```text
============================= test session starts =============================
platform win32 -- Python 3.12.13, pytest-9.0.3, pluggy-1.6.0 -- C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase0\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system
collecting ... collected 23 items

xau-usd/xauusd-phase1/tests/test_a3_executors_source.py::test_a3_committed_defaults_are_non_executing PASSED [  4%]
xau-usd/xauusd-phase1/tests/test_a3_executors_source.py::test_a3_magic_bands_and_reserved_band_are_source_locked PASSED [  8%]
xau-usd/xauusd-phase1/tests/test_a3_executors_source.py::test_no_committed_a3_execution_enabled_preset_anywhere PASSED [ 13%]
xau-usd/xauusd-phase1/tests/test_a3_executors_source.py::test_a3_login_allowlist_demo_server_live_real_refusal_and_kill_switch PASSED [ 17%]
xau-usd/xauusd-phase1/tests/test_a3_executors_source.py::test_a3_t1_impulse_formula_and_logging_are_present PASSED [ 21%]
xau-usd/xauusd-phase1/tests/test_a3_executors_source.py::test_a3_t2_has_structure_filter_and_no_impulse_veto PASSED [ 26%]
xau-usd/xauusd-phase1/tests/test_a3_executors_source.py::test_a3_required_reason_codes_present PASSED [ 30%]
xau-usd/xauusd-phase1/tests/test_a3_executors_source.py::test_a3_signal_rows_include_confluence_fields PASSED [ 34%]
xau-usd/xauusd-phase1/tests/test_a3_executors_source.py::test_a3_gv_mutex_claim_occurs_before_order_send PASSED [ 39%]
xau-usd/xauusd-phase1/tests/test_a3_executors_source.py::test_a3_executors_write_startup_gv_mutex_self_test_rows PASSED [ 43%]
xau-usd/xauusd-phase1/tests/test_a3_executors_source.py::test_a3_eas_have_no_position_management_or_order_deletion_calls PASSED [ 47%]
xau-usd/xauusd-phase1/tests/test_a3_executors_source.py::test_a3_eas_are_xauusd_only PASSED [ 52%]
xau-usd/xauusd-phase1/tests/test_a3_executors_source.py::test_a3_streak_daily_and_g5_constants_match_locked_parameters PASSED [ 56%]
xau-usd/xauusd-phase1/tests/test_a3_executors_source.py::test_a3_hypothesis_manifest_hashes_match_files PASSED [ 60%]
xau-usd/xauusd-phase1/tests/test_a3_executor_presets.py::test_a3_safe_presets_are_committed_non_executing PASSED [ 65%]
xau-usd/xauusd-phase1/tests/test_a3_executor_presets.py::test_no_committed_a3_execution_enabled_preset PASSED [ 69%]
xau-usd/xauusd-phase1/tests/test_a3_review_reports.py::test_a3_review_reports_include_evening_pnl_line PASSED [ 73%]
xau-usd/xauusd-phase1/tests/test_a3_review_reports.py::test_a3_review_reports_summarize_evening_standdown_shadow PASSED [ 78%]
xau-usd/xauusd-phase1/tests/test_a3_review_reports.py::test_a3_review_reports_include_confluence_breakdown PASSED [ 82%]
xau-usd/xauusd-phase1/tests/test_a3_runtime_reports.py::test_a3_runtime_reports_generate_fixed_names PASSED [ 86%]
xau-usd/xauusd-phase1/tests/test_phase2_experimental_demo_mutex.py::test_a1_executor_claims_gv_mutex_before_order_send PASSED [ 91%]
xau-usd/xauusd-phase1/tests/test_phase2_experimental_demo_mutex.py::test_a1_executor_mutex_namespace_and_expiry_are_source_locked PASSED [ 95%]
xau-usd/xauusd-phase1/tests/test_phase2_experimental_demo_mutex.py::test_a1_executor_writes_startup_gv_mutex_self_test_row PASSED [100%]

============================= 23 passed in 0.59s ==============================
```

## Compile Output

COMMAND:

```text
C:\MT5PortableRepairLane\MetaEditor64.exe /compile:C:\MT5CompileScratch\A3GvSelftest_20260613_230048\MQL5\Experts\Account3RoundRetestGuardedExecutor.mq5 /log:C:\MT5CompileScratch\A3GvSelftest_20260613_230048\Logs\compile_Account3RoundRetestGuardedExecutor.log
C:\MT5PortableRepairLane\MetaEditor64.exe /compile:C:\MT5CompileScratch\A3GvSelftest_20260613_230048\MQL5\Experts\Account3RoundRetestStructuredExecutor.mq5 /log:C:\MT5CompileScratch\A3GvSelftest_20260613_230048\Logs\compile_Account3RoundRetestStructuredExecutor.log
```

EA-T1 log:

```text
C:\MT5CompileScratch\A3GvSelftest_20260613_230048\MQL5\Experts\Account3RoundRetestGuardedExecutor.mq5 : information: compiling C:\MT5CompileScratch\A3GvSelftest_20260613_230048\MQL5\Experts\Account3RoundRetestGuardedExecutor.mq5
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
Result: 0 errors, 0 warnings, 762 ms elapsed, cpu='X64 Regular'
```

EA-T2 log:

```text
C:\MT5CompileScratch\A3GvSelftest_20260613_230048\MQL5\Experts\Account3RoundRetestStructuredExecutor.mq5 : information: compiling C:\MT5CompileScratch\A3GvSelftest_20260613_230048\MQL5\Experts\Account3RoundRetestStructuredExecutor.mq5
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
Result: 0 errors, 0 warnings, 759 ms elapsed, cpu='X64 Regular'
```

## Armed Presets

COMMAND:

```text
Get-Content C:\MT5PortableRepairLane\MQL5\Presets\Account3RoundRetestGuardedExecutor.armed_owner_20260614.set
Get-Content C:\MT5PortableRepairLane\MQL5\Presets\Account3RoundRetestStructuredExecutor.armed_owner_20260614.set
```

OUTPUT:

```text
InpRunId=A3_RDGUARD_V1_SAFE
InpDryRunOnly=false
InpBrokerActionAllowed=true
InpTargetSymbol=XAUUSD
InpExpectedServerMarker=Demo
InpAllowedAccountLoginsCsv=1033669
InpKillSwitchFileName=A3_KILL.txt
InpMagicNumber=933000
InpOrderComment=RDGUARD_V1
InpSignalLogFileName=a3_rdguard_v1_signal_log.csv
InpStartupLogFileName=a3_rdguard_v1_startup.csv
InpOrderLogFileName=a3_rdguard_v1_order_log.csv
InpImpulseVetoThreshold=-1.5
InpStreakLossCount=3
InpStreakWindowMinutes=120
InpDubaiUtcOffsetMinutes=240
InpDailyLossStopAed=-150.0
InpMaxOpenPositionsPerMagic=1
InpMaxEstimatedCostR=0.15
InpCostWarnR=0.20
InpAbsoluteRejectCostR=0.30
InpMaxMeasuredSpreadPoints=75.0
InpMinSecondsBetweenOrders=60
InpFixedLot=0.01
InpDeviationPoints=50
InpRunId=A3_RDSTRUCT_V1_SAFE
InpDryRunOnly=false
InpBrokerActionAllowed=true
InpTargetSymbol=XAUUSD
InpExpectedServerMarker=Demo
InpAllowedAccountLoginsCsv=1033669
InpKillSwitchFileName=A3_KILL.txt
InpMagicNumber=933100
InpOrderComment=RDSTRUCT_V1
InpSignalLogFileName=a3_rdstruct_v1_signal_log.csv
InpStartupLogFileName=a3_rdstruct_v1_startup.csv
InpOrderLogFileName=a3_rdstruct_v1_order_log.csv
InpM15StructureLookbackBars=20
InpSwingConfirmLeftBars=4
InpSwingConfirmRightBars=4
InpStreakLossCount=3
InpStreakWindowMinutes=120
InpDubaiUtcOffsetMinutes=240
InpDailyLossStopAed=-150.0
InpMaxOpenPositionsPerMagic=1
InpMaxEstimatedCostR=0.15
InpCostWarnR=0.20
InpAbsoluteRejectCostR=0.30
InpMaxMeasuredSpreadPoints=75.0
InpMinSecondsBetweenOrders=60
InpFixedLot=0.01
InpDeviationPoints=50
```

## Detach And Reattach Evidence

Detach summary was written to `C:\MT5PortableRepairLane\MQL5\Files\gv_selftest_parity_detach_20260613_225705.json`.

```json
{
  "created_at_utc": "2026-06-13T22:57:14.086870Z",
  "created_at_local": "2026-06-14T02:57:14+04:00",
  "repair_processes_before": [
    {
      "ProcessId": 12928,
      "ExecutablePath": "C:\\MT5PortableRepairLane\\terminal64.exe",
      "CommandLine": "C:\\MT5PortableRepairLane\\terminal64.exe /portable /config:C:\\MT5PortableRepairLane\\Config\\a3_arm_attach_startup.ini"
    }
  ],
  "repair_processes_after": [],
  "before": {
    "startup_counts": {"EA-T1": 5, "EA-T2": 5},
    "signal_counts": {"EA-T1": 1, "EA-T2": 1},
    "order_counts": {"EA-T1": 0, "EA-T2": 0}
  },
  "after": {
    "startup_counts": {"EA-T1": 6, "EA-T2": 6},
    "signal_counts": {"EA-T1": 1, "EA-T2": 1},
    "order_counts": {"EA-T1": 0, "EA-T2": 0},
    "latest_startup": {
      "EA-T1": {"timestamp_utc": "2026.06.13 22:57:06", "timestamp_local": "2026.06.14 02:57:06", "startup_status": "REMOVED_REASON_9"},
      "EA-T2": {"timestamp_utc": "2026.06.13 22:57:06", "timestamp_local": "2026.06.14 02:57:06", "startup_status": "REMOVED_REASON_9"}
    }
  },
  "xauusd_m5_before": {"rows": 2736, "last": "2026-06-12 20:55:00"},
  "xauusd_m5_after": {"rows": 2736, "last": "2026-06-12 20:55:00"}
}
```

Relaunch watcher output:

```json
{
  "baseline": {
    "start_utc": "2026.06.13 23:02:27",
    "start_local": "2026.06.14 03:02:27",
    "guard_startup_count": 6,
    "struct_startup_count": 6,
    "guard_signal_count": 1,
    "struct_signal_count": 1,
    "guard_order_count": 0,
    "struct_order_count": 0,
    "m5_rows": 2736,
    "m5_last": "2026-06-12 20:55:00"
  },
  "after": {
    "end_utc": "2026.06.13 23:02:31",
    "end_local": "2026.06.14 03:02:31",
    "process_id": 21660,
    "process_running": true,
    "guard_startup_count": 8,
    "struct_startup_count": 8,
    "guard_signal_count": 2,
    "struct_signal_count": 2,
    "guard_order_count": 0,
    "struct_order_count": 0,
    "m5_rows": 2736,
    "m5_last": "2026-06-12 20:55:00"
  }
}
```

## Startup Rows

COMMAND:

```text
Get-Content C:\MT5PortableRepairLane\MQL5\Files\a3_rdguard_v1_startup.csv -Tail 4
Get-Content C:\MT5PortableRepairLane\MQL5\Files\a3_rdstruct_v1_startup.csv -Tail 4
```

OUTPUT:

```text
2026.06.12 20:59:57,2026.06.13 22:31:19,2026.06.14 02:31:19,A3_RDGUARD_V1_SAFE,Capital.ComMena-Demo,1033669,XAUUSD,933000,RDGUARD_V1,1033669,false,true,0.01,1,0.1500,0.2000,0.3000,75.00,60,A3_KILL.txt,ATTACHED_A3_RDGUARD_V1
2026.06.12 20:59:57,2026.06.13 22:57:06,2026.06.14 02:57:06,A3_RDGUARD_V1_SAFE,Capital.ComMena-Demo,1033669,XAUUSD,933000,RDGUARD_V1,1033669,false,true,0.01,1,0.1500,0.2000,0.3000,75.00,60,A3_KILL.txt,REMOVED_REASON_9
2026.06.12 20:59:57,2026.06.13 23:02:29,2026.06.14 03:02:29,A3_RDGUARD_V1_SAFE,Capital.ComMena-Demo,1033669,XAUUSD,933000,RDGUARD_V1,1033669,false,true,0.01,1,0.1500,0.2000,0.3000,75.00,60,A3_KILL.txt,GV_MUTEX_NAMESPACE_SELF_TEST_PASS name=FAMMUX_SELFTEST_RD_1033669_20260613_230229
2026.06.12 20:59:57,2026.06.13 23:02:29,2026.06.14 03:02:29,A3_RDGUARD_V1_SAFE,Capital.ComMena-Demo,1033669,XAUUSD,933000,RDGUARD_V1,1033669,false,true,0.01,1,0.1500,0.2000,0.3000,75.00,60,A3_KILL.txt,ATTACHED_A3_RDGUARD_V1
2026.06.12 20:59:57,2026.06.13 22:31:19,2026.06.14 02:31:19,A3_RDSTRUCT_V1_SAFE,Capital.ComMena-Demo,1033669,XAUUSD,933100,RDSTRUCT_V1,1033669,false,true,0.01,1,0.1500,0.2000,0.3000,75.00,60,A3_KILL.txt,ATTACHED_A3_RDSTRUCT_V1
2026.06.12 20:59:57,2026.06.13 22:57:06,2026.06.14 02:57:06,A3_RDSTRUCT_V1_SAFE,Capital.ComMena-Demo,1033669,XAUUSD,933100,RDSTRUCT_V1,1033669,false,true,0.01,1,0.1500,0.2000,0.3000,75.00,60,A3_KILL.txt,REMOVED_REASON_9
2026.06.12 20:59:57,2026.06.13 23:02:29,2026.06.14 03:02:29,A3_RDSTRUCT_V1_SAFE,Capital.ComMena-Demo,1033669,XAUUSD,933100,RDSTRUCT_V1,1033669,false,true,0.01,1,0.1500,0.2000,0.3000,75.00,60,A3_KILL.txt,GV_MUTEX_NAMESPACE_SELF_TEST_PASS name=FAMMUX_SELFTEST_RDSTRUCT_1033669_20260613_230229
2026.06.12 20:59:57,2026.06.13 23:02:29,2026.06.14 03:02:29,A3_RDSTRUCT_V1_SAFE,Capital.ComMena-Demo,1033669,XAUUSD,933100,RDSTRUCT_V1,1033669,false,true,0.01,1,0.1500,0.2000,0.3000,75.00,60,A3_KILL.txt,ATTACHED_A3_RDSTRUCT_V1
```

## Latest Signal Rows

The reattach produced one fresh `NO_SIGNAL` row per EA on the same closed-market M5 bar. No orders were written.

```text
2026.06.12 20:59:57,2026.06.13 23:02:30,2026.06.14 03:02:30,A3_RDGUARD_V1_SAFE,Capital.ComMena-Demo,1033669,XAUUSD,933000,RDGUARD_V1,2026.06.12 20:55:00,4218.54,4219.29,75.00,WAIT_LEVEL_BREAK_RETEST,LONG,false,no_long_symbol_normalized_round_retest_v0_candidate,NO_SIGNAL,false,none,0.00,0.00,0.00,0.00,0.00,3.776831,3.776831,0.0000,,0,0,1970.01.01 00:00:00,0.00,1970.01.01 00:00:00,,,0,false,true
2026.06.12 20:59:57,2026.06.13 23:02:30,2026.06.14 03:02:30,A3_RDSTRUCT_V1_SAFE,Capital.ComMena-Demo,1033669,XAUUSD,933100,RDSTRUCT_V1,2026.06.12 20:55:00,4218.54,4219.29,75.00,WAIT_LEVEL_BREAK_RETEST,LONG,false,no_long_symbol_normalized_round_retest_v0_candidate,NO_SIGNAL,false,none,0.00,0.00,0.00,0.00,0.00,true,29,2026.06.12 13:30:00,LONG,4209.95,4221.53,1158.00,0.0000,,0,0,1970.01.01 00:00:00,0.00,1970.01.01 00:00:00,,,0,false,true
```

## MT5 Read-Only Query

COMMAND:

```text
MetaTrader5.initialize(path="C:\\MT5PortableRepairLane\\terminal64.exe", portable=True); account_info(); positions_get(); orders_get()
```

OUTPUT:

```json
{
  "initialize": true,
  "last_error": [1, "Success"],
  "account_login": 1033669,
  "account_server": "Capital.ComMena-Demo",
  "balance": 4000.0,
  "positions_total": 0,
  "orders_total": 0,
  "target_positions": [],
  "target_orders": []
}
```

## Terminal Journal

```text
MK	0	03:02:27.973	Startup	successfully initialized from start config "C:\MT5PortableRepairLane\Config\a3_arm_attach_startup.ini"
IF	0	03:02:27.992	Terminal	MetaTrader 5 x64 build 5833 started for MetaQuotes Ltd.
OL	0	03:02:27.992	Terminal	C:\MT5PortableRepairLane
RK	0	03:02:27.992	Terminal	launched with C:\MT5PortableRepairLane\Config\a3_arm_attach_startup.ini
KF	0	03:02:28.930	Experts	expert Account3RoundRetestGuardedExecutor (XAUUSD,M5) loaded successfully
HL	0	03:02:28.950	Experts	expert Account3RoundRetestStructuredExecutor (XAUUSD,M5) loaded successfully
JS	0	03:02:29.316	Network	'1033669': authorized on Capital.ComMena-Demo through Access Point 2 (ping: 130.83 ms, build 5800)
LQ	0	03:02:29.711	Network	'1033669': terminal synchronized with Capital Com Mena Securities Trading L.L.C: 0 positions, 0 orders, 232 symbols, 0 spreads
OQ	0	03:02:29.711	Network	'1033669': trading has been enabled - hedging mode
```

## Process Scope

COMMAND:

```text
Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'terminal64.exe' } | Select-Object ProcessId,ExecutablePath,CommandLine | ConvertTo-Json -Depth 4
```

OUTPUT:

```json
[
  {"ProcessId":21248,"ExecutablePath":"C:\\MT5PortableGoldMission\\terminal64.exe","CommandLine":"\"C:\\MT5PortableGoldMission\\terminal64.exe\" /portable /config:C:\\MT5PortableGoldMission\\Config\\phase1_dry_run_startup.ini "},
  {"ProcessId":16092,"ExecutablePath":"C:\\MT5PortableSpreadLogger\\terminal64.exe","CommandLine":"\"C:\\MT5PortableSpreadLogger\\terminal64.exe\" /portable /config:C:\\MT5PortableSpreadLogger\\Config\\phase0_spread_logger_startup.ini "},
  {"ProcessId":3144,"ExecutablePath":"C:\\MT5PortableShadowFixObservers\\terminal64.exe","CommandLine":"\"C:\\MT5PortableShadowFixObservers\\terminal64.exe\" /portable "},
  {"ProcessId":17200,"ExecutablePath":"C:\\MT5PortableTrendGuardedFixObservers\\terminal64.exe","CommandLine":"\"C:\\MT5PortableTrendGuardedFixObservers\\terminal64.exe\" /portable "},
  {"ProcessId":11724,"ExecutablePath":"C:\\MT5PortablePositionPathObserver\\terminal64.exe","CommandLine":"\"C:\\MT5PortablePositionPathObserver\\terminal64.exe\" /portable "},
  {"ProcessId":13232,"ExecutablePath":"C:\\MT5PortableTier1PathObserver\\terminal64.exe","CommandLine":"C:\\MT5PortableTier1PathObserver\\terminal64.exe /portable /config:C:\\MT5PortableTier1PathObserver\\Config\\position_path_observer_startup.ini"},
  {"ProcessId":8780,"ExecutablePath":"C:\\MT5PortableTier1BestEA\\terminal64.exe","CommandLine":"\"C:\\MT5PortableTier1BestEA\\terminal64.exe\" /portable /config:C:\\MT5PortableTier1BestEA\\Config\\tier1_bestea_startup.ini "},
  {"ProcessId":17676,"ExecutablePath":"C:\\Program Files\\MetaTrader 5\\terminal64.exe","CommandLine":"\"C:\\Program Files\\MetaTrader 5\\terminal64.exe\" "},
  {"ProcessId":21660,"ExecutablePath":"C:\\MT5PortableRepairLane\\terminal64.exe","CommandLine":"\"C:\\MT5PortableRepairLane\\terminal64.exe\" /portable /config:C:\\MT5PortableRepairLane\\Config\\a3_arm_attach_startup.ini "}
]
```

## Git Scope

COMMAND:

```text
git diff --name-only
```

OUTPUT:

```text
status.html
xau-usd/xauusd-phase1/mt5/Experts/Account3RoundRetestGuardedExecutor.mq5
xau-usd/xauusd-phase1/mt5/Experts/Account3RoundRetestStructuredExecutor.mq5
xau-usd/xauusd-phase1/outputs/reports/PHASE2_DEMO_REPAIR_FORWARD_WEEK_REPORT.json
xau-usd/xauusd-phase1/outputs/reports/PHASE2_DEMO_REPAIR_FORWARD_WEEK_REPORT.md
xau-usd/xauusd-phase1/outputs/reports/PHASE2_DEMO_REPAIR_MONITOR_LATEST.json
xau-usd/xauusd-phase1/outputs/reports/PHASE2_DEMO_REPAIR_MONITOR_LATEST.md
xau-usd/xauusd-phase1/tests/test_a3_executors_source.py
```

The `status.html` and `PHASE2_DEMO_REPAIR_*` files were pre-existing unrelated dirty files and were not staged for this task. This task changed only the two A3 EA sources, the A3 parity test, this report, the A3 combined preflight report, and the A3 arm/attach report.
