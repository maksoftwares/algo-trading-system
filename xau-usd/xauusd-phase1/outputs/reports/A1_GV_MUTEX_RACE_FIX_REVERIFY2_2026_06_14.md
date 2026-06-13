# A1 GV Mutex Race Fix Reverify2

Status: `PASS_IN_THIS_CHECKOUT`

This report supersedes `A1_GV_MUTEX_RACE_FIX_REVERIFY_2026_06_14.md`.

## Global Boundaries

- A3 demo login `1033669`.
- A2 (`1033030`) untouched.
- A1 (`1025742`) touched only for the T0 mutex fix.
- Demo only; no live trading; canonical Phase 2 status unchanged.
- All committed defaults remain non-executing: `InpDryRunOnly=true`, `InpBrokerActionAllowed=false`.
- A3 combined preflight and attach status remain `DO_NOT_ATTACH`.

## Start Checkout State

Raw output from `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system`:

```text
COMMAND: git rev-parse --show-toplevel
C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system
COMMAND: git rev-parse HEAD
2efa5d4461a68a37e58d9db8ff47bce2a78de6c1
COMMAND: git status --porcelain
 M status.html
 M xau-usd/xauusd-phase1/outputs/reports/PHASE2_DEMO_REPAIR_FORWARD_WEEK_REPORT.json
 M xau-usd/xauusd-phase1/outputs/reports/PHASE2_DEMO_REPAIR_FORWARD_WEEK_REPORT.md
 M xau-usd/xauusd-phase1/outputs/reports/PHASE2_DEMO_REPAIR_MONITOR_LATEST.json
 M xau-usd/xauusd-phase1/outputs/reports/PHASE2_DEMO_REPAIR_MONITOR_LATEST.md
?? CODEX_ADDENDUM_EVENING_SESSION_AND_CONFLUENCE_2026_06_13.md
?? CODEX_WORK_ORDER_A3_REPAIR_LANE_2026_06_13.md
?? CODEX_WORK_ORDER_ADDENDUM2_EAT2_EAT3PREP_2026_06_13.md
?? CODEX_WORK_ORDER_T0_T12_REVERIFY_DISCREPANCY_2026_06_14.md
?? DEEP_DIVE_PROFIT_DUPLICATION_AND_CONSENSUS_2026_06_13.md
?? EVENING_SESSION_POSITIVE_GOAL_PLAN_2026_06_13.md
?? PORTFOLIO_AND_FIXED_EA_DEPLOYMENT_PLAN_2026_06_13.md
```

## Required T0 Raw Checks

Raw output from `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1`:

```text
COMMAND: git rev-parse HEAD
2efa5d4461a68a37e58d9db8ff47bce2a78de6c1
COMMAND: wc -l mt5/Experts/Phase2ExperimentalDemoExecutor.mq5
COMMAND: sha256sum mt5/Experts/Phase2ExperimentalDemoExecutor.mq5
COMMAND: git diff --stat -- mt5/Experts/Phase2ExperimentalDemoExecutor.mq5
COMMAND: native PowerShell line/hash/diff equivalent


LineCount    : 1630
SHA256       : a04123fd590303b9fa576c485883ae54b67fbb9066336e37ef8fae31904290ce
DiffNameOnly :



wc : The term 'wc' is not recognized as the name of a cmdlet, function, script file, or operable program. Check the
spelling of the name, or if a path was included, verify that the path is correct and try again.
At line:6 char:1
+ wc -l mt5/Experts/Phase2ExperimentalDemoExecutor.mq5
+ ~~
    + CategoryInfo          : ObjectNotFound: (wc:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException

sha256sum : The term 'sha256sum' is not recognized as the name of a cmdlet, function, script file, or operable
program. Check the spelling of the name, or if a path was included, verify that the path is correct and try again.
At line:8 char:1
+ sha256sum mt5/Experts/Phase2ExperimentalDemoExecutor.mq5
+ ~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (sha256sum:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
```

Result in this checkout: the executor is not truncated. It has 1630 lines, SHA-256 `a04123fd590303b9fa576c485883ae54b67fbb9066336e37ef8fae31904290ce`, and no diff for `mt5/Experts/Phase2ExperimentalDemoExecutor.mq5`.

## Source Landmarks And Mtime

Raw output:

```text
C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\mt5\Experts\Phase2ExperimentalDemoExecutor.mq5:1403:if(!ClaimFamilyMutexBeforeOrder(observation, mutex_name))
C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\mt5\Experts\Phase2ExperimentalDemoExecutor.mq5:1425:bool sent = OrderSend(request, result);
C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\mt5\Experts\Phase2ExperimentalDemoExecutor.mq5:1455:int OnInit()
C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\mt5\Experts\Phase2ExperimentalDemoExecutor.mq5:1524:WriteStartupRow(gv_mutex_self_test_status);
C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\mt5\Experts\Phase2ExperimentalDemoExecutor.mq5:1527:WriteStartupRow(gv_mutex_self_test_status);
C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\mt5\Experts\Phase2ExperimentalDemoExecutor.mq5:1536:void OnDeinit(const int reason)
C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\mt5\Experts\Phase2ExperimentalDemoExecutor.mq5:1567:void OnTimer()


FullName         : C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\mt5\Experts\Phase2
                   ExperimentalDemoExecutor.mq5
Length           : 52003
LastWriteTime    : 6/14/2026 12:16:55 AM
LastWriteTimeUtc : 6/13/2026 8:16:55 PM
```

`int OnInit()`, `void OnDeinit(const int reason)`, and `void OnTimer()` are present in that order. The mutex claim precedes `OrderSend`.

## Pytest

The requested `python3` command is not usable on this Windows checkout:

```text
COMMAND: python3 -m pytest tests/test_phase2_experimental_demo_mutex.py -v
Python was not found; run without arguments to install from the Microsoft Store, or disable this shortcut from Settings > Apps > Advanced app settings > App execution aliases.
```

Equivalent repo venv command actually run:

```text
..\xauusd-phase0\.venv\Scripts\python.exe -m pytest tests\test_phase2_experimental_demo_mutex.py -v
```

Raw output:

```text
============================= test session starts =============================
platform win32 -- Python 3.12.13, pytest-9.0.3, pluggy-1.6.0 -- C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase0\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1
collecting ... collected 3 items

tests/test_phase2_experimental_demo_mutex.py::test_a1_executor_claims_gv_mutex_before_order_send PASSED [ 33%]
tests/test_phase2_experimental_demo_mutex.py::test_a1_executor_mutex_namespace_and_expiry_are_source_locked PASSED [ 66%]
tests/test_phase2_experimental_demo_mutex.py::test_a1_executor_writes_startup_gv_mutex_self_test_row PASSED [100%]

============================== 3 passed in 0.03s ==============================
```

## MetaEditor Compile

Compile summary:

```text
{
    "scratch":  "C:\\MT5CompileScratch\\A1GvMutexReverify2_20260614_020156",
    "source":  "C:\\MT5CompileScratch\\A1GvMutexReverify2_20260614_020156\\MQL5\\Experts\\Phase2ExperimentalDemoExecutor.mq5",
    "log":  "C:\\MT5CompileScratch\\A1GvMutexReverify2_20260614_020156\\Logs\\compile_Phase2ExperimentalDemoExecutor.log",
    "ex5_path":  "C:\\MT5CompileScratch\\A1GvMutexReverify2_20260614_020156\\MQL5\\Experts\\Phase2ExperimentalDemoExecutor.ex5",
    "ex5_exists":  true,
    "ex5_mtime":  "2026-06-14 02:01:58 +04:00",
    "ex5_mtime_utc":  "2026-06-13T22:01:58Z",
    "result":  "Result: 0 errors, 0 warnings, 978 ms elapsed, cpu='X64 Regular'",
    "exit_code":  1
}
```

Full compile log contents:

```text
C:\MT5CompileScratch\A1GvMutexReverify2_20260614_020156\MQL5\Experts\Phase2ExperimentalDemoExecutor.mq5 : information: compiling C:\MT5CompileScratch\A1GvMutexReverify2_20260614_020156\MQL5\Experts\Phase2ExperimentalDemoExecutor.mq5
C:\MT5CompileScratch\A1GvMutexReverify2_20260614_020156\MQL5\Experts\Phase2ExperimentalDemoExecutor.mq5 : information: including C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Include\Phase1\Phase1Types.mqh
C:\MT5CompileScratch\A1GvMutexReverify2_20260614_020156\MQL5\Experts\Phase2ExperimentalDemoExecutor.mq5 : information: including C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Include\Phase1\Phase1BreakoutRetest.mqh
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
Result: 0 errors, 0 warnings, 978 ms elapsed, cpu='X64 Regular'
```

MetaEditor process exit code was `1`, but the compile log reports `0 errors, 0 warnings` and the `.ex5` artifact exists at:

```text
C:\MT5CompileScratch\A1GvMutexReverify2_20260614_020156\MQL5\Experts\Phase2ExperimentalDemoExecutor.ex5
mtime local: 2026-06-14 02:01:58 +04:00
mtime UTC:   2026-06-13T22:01:58Z
```

## End Checkout State Before This Report Commit

Raw output from `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system`:

```text
COMMAND: git rev-parse --show-toplevel
C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system
COMMAND: git rev-parse HEAD
2efa5d4461a68a37e58d9db8ff47bce2a78de6c1
COMMAND: git status --porcelain
 M status.html
 M xau-usd/xauusd-phase1/outputs/reports/PHASE2_DEMO_REPAIR_FORWARD_WEEK_REPORT.json
 M xau-usd/xauusd-phase1/outputs/reports/PHASE2_DEMO_REPAIR_FORWARD_WEEK_REPORT.md
 M xau-usd/xauusd-phase1/outputs/reports/PHASE2_DEMO_REPAIR_MONITOR_LATEST.json
 M xau-usd/xauusd-phase1/outputs/reports/PHASE2_DEMO_REPAIR_MONITOR_LATEST.md
?? CODEX_ADDENDUM_EVENING_SESSION_AND_CONFLUENCE_2026_06_13.md
?? CODEX_WORK_ORDER_A3_REPAIR_LANE_2026_06_13.md
?? CODEX_WORK_ORDER_ADDENDUM2_EAT2_EAT3PREP_2026_06_13.md
?? CODEX_WORK_ORDER_T0_T12_REVERIFY_DISCREPANCY_2026_06_14.md
?? DEEP_DIVE_PROFIT_DUPLICATION_AND_CONSENSUS_2026_06_13.md
?? EVENING_SESSION_POSITIVE_GOAL_PLAN_2026_06_13.md
?? PORTFOLIO_AND_FIXED_EA_DEPLOYMENT_PLAN_2026_06_13.md
```

## Result

No T0 source repair was required in this checkout. The executor file is complete, unchanged versus HEAD, compiles cleanly by MetaEditor log, and the focused mutex suite passes.
