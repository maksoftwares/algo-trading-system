# A1 GV Mutex Race Fix

Overall status: PASS

## Global Boundaries

- A3 demo account login: `1033669`.
- Demo only. No live trading. Canonical Phase 2 status unchanged.
- A2 (`1033030`, `breakout_retest`) was not touched.
- A1 (`1025742`) was touched only for T0's owed GV-lock mutex race fix.
- All committed defaults remain non-executing. Broker action still arms only through local owner/runtime presets.
- Locked hypotheses were not edited.

## Source Change

`Phase2ExperimentalDemoExecutor.mq5` now claims a per-family/per-symbol/per-direction/per-M5-bar mutex with:

`GlobalVariableSetOnCondition(mutex_name, (double)magic, 0.0)`

The mutex name is `FAMMUX_<family><symbol><direction><m5_bar_time>`. The claim happens after normal guards and request validation but before `OrderSend`. A claim failure logs `WOULD_DUPLICATE_FAMILY_EVENT`. The EA holds its own claim until the M5 bar expires; the bar timestamp is part of the key, so stale claims cannot block later bars.

Startup now writes a GV namespace self-test row, either `GV_MUTEX_NAMESPACE_SELF_TEST_PASS` or `GV_MUTEX_NAMESPACE_SELF_TEST_FAIL`, before the normal attachment row.

## Runtime Maintenance

| Item | Evidence |
|---|---|
| A1 terminal | `C:/Program Files/MetaTrader 5/terminal64.exe` |
| A1 data root | `C:/Users/ZHAO ZHU INFORMATION/AppData/Roaming/MetaQuotes/Terminal/D0E8209F77C8CF37AD8BF550E51FF075` |
| Backup | `C:/Users/ZHAO ZHU INFORMATION/AppData/Roaming/MetaQuotes/Terminal/D0E8209F77C8CF37AD8BF550E51FF075/_codex_quarantine/a1_gv_mutex_fix_20260614_001832` |
| Terminal closed before deploy | `true` |
| Terminal relaunched | `true` |
| Compile log | `C:/Users/ZHAO ZHU INFORMATION/AppData/Roaming/MetaQuotes/Terminal/D0E8209F77C8CF37AD8BF550E51FF075/MQL5/Logs/compile_Phase2ExperimentalDemoExecutor_a1_gv_mutex.log` |
| Compile result | `Result: 0 errors, 0 warnings, 997 ms elapsed, cpu='X64 Regular'` |
| Startup self-test rows before | `0` |
| Startup self-test rows after | `14` |
| Latest self-test | `GV_MUTEX_NAMESPACE_SELF_TEST_PASS name=FAMMUX_SELFTEST_1025742_20260613_201852` |

## Verification

- Focused pytest: `tests/test_phase2_experimental_demo_mutex.py` - 3 passed.
- Scratch compile: `C:/MT5CompileScratch/A1GvMutex_20260614_001736/Logs/compile_Phase2ExperimentalDemoExecutor.log` - 0 errors, 0 warnings.

## Result

A1 control data should no longer be duplicate-contaminated by same-family same-direction races within an M5 bar.
