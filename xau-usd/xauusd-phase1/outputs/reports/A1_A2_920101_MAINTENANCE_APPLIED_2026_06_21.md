# A1/A2 920101 Maintenance Applied - 2026-06-21

Status: `FAIL_APPLIED`
Mode: `apply`

Owner requested fixing runtime drift after forensic confirmation. Demo accounts only; no canonical Phase 2/live-capital approval.

## Scope

- A1 account: `1025742`
- A2 account: `1033030`
- Symbol/candidate: `XAUUSD / breakout_retest`
- Session server hours: `12->15`
- Lot: `0.01`
- Smart trend filter: `enabled=true shadow_only=false D1>=0.25 H1>=0.35`
- Daily floor / next floor: `50.0 / 100.0`
- A3 touched: `False`

## Checks

| Check | Status | Detail |
| --- | --- | --- |
| a1_has_one_active_xau_920101_chart | `FAIL` | chart03.chr,chart27.chr |
| a2_has_one_active_xau_920101_chart | `FAIL` | chart02.chr,chart04.chr |
| a1_non_spec_executors_disarmed | `PASS` | A1 non-spec broker action false/dry-run true |
| a1_wr50_disarmed | `PASS` | WR50 demo trading disabled |
| a1_guardian_active_loss_stop | `PASS` | A1 guardian active with -100 loss stop |
| a2_guardian_active_loss_stop | `PASS` | A2 guardian active with -100 loss stop |
| a3_profile_untouched | `PASS` | A3 profile hash map unchanged |
| profile_backups_created | `PASS` | {"A1": "C:\\Users\\ZHAO ZHU INFORMATION\\AppData\\Roaming\\MetaQuotes\\Terminal\\D0E8209F77C8CF37AD8BF550E51FF075\\_codex_quarantine\\profile_backups\\a1_a2_920101_maintenance_a1_20260628_153321", "A2": "C:\\MT5PortableTier1BestEA\\_codex_quarantine\\profile_backups\\a1_a2_920101_maintenance_a2_20260628_153322"} |
| terminals_stopped_before_write | `PASS` | [{"action": "stop", "after": {"pids": [], "running": false}, "before": {"pids": [22620], "running": true}, "lane": "A1", "status": "PASS"}, {"action": "stop", "after": {"pids": [], "running": false}, "before": {"pids": [25140], "running": true}, "lane": "A2", "status": "PASS"}, {"action": "launch", "lane": "A1", "portable": "False", "status": "PASS", "terminal": "C:\\Program Files\\MetaTrader 5\\terminal64.exe"}, {"action": "launch", "lane": "A2", "portable": "True", "status": "PASS", "terminal": "C:\\MT5PortableTier1BestEA\\terminal64.exe"}] |
| compile_reports_pass | `PASS` | [{"ea": "Phase2ExperimentalDemoExecutor", "ex5": "C:\\Users\\ZHAO ZHU INFORMATION\\AppData\\Roaming\\MetaQuotes\\Terminal\\D0E8209F77C8CF37AD8BF550E51FF075\\MQL5\\Experts\\Phase2ExperimentalDemoExecutor.ex5", "log": "C:\\Users\\ZHAO ZHU INFORMATION\\AppData\\Roaming\\MetaQuotes\\Terminal\\D0E8209F77C8CF37AD8BF550E51FF075\\MQL5\\Logs\\compile_Phase2ExperimentalDemoExecutor_a1_a2_920101_20260621.log", "log_tail": [" : information: generating code 72%", " : information: generating code 75%", " : information: generating code 78%", " : information: generating code 81%", " : information: generating code 84%", " : information: generating code 87%", " : information: generating code 90%", " : information: generating code 93%", " : information: generating code 95%", " : information: generating code 100%", " : information: code generated", "Result: 0 errors, 0 warnings, 1452 ms elapsed, cpu='X64 Regular'"], "status": "PASS", "terminal_data": "C:\\Users\\ZHAO ZHU INFORMATION\\AppData\\Roaming\\MetaQuotes\\Terminal\\D0E8209F77C8CF37AD8BF550E51FF075"}, {"ea": "Account1DailyProfitFloorGuardian", "ex5": "C:\\Users\\ZHAO ZHU INFORMATION\\AppData\\Roaming\\MetaQuotes\\Terminal\\D0E8209F77C8CF37AD8BF550E51FF075\\MQL5\\Experts\\Account1DailyProfitFloorGuardian.ex5", "log": "C:\\Users\\ZHAO ZHU INFORMATION\\AppData\\Roaming\\MetaQuotes\\Terminal\\D0E8209F77C8CF37AD8BF550E51FF075\\MQL5\\Logs\\compile_Account1DailyProfitFloorGuardian_a1_a2_920101_20260621.log", "log_tail": [" : information: generating code 72%", " : information: generating code 75%", " : information: generating code 78%", " : information: generating code 81%", " : information: generating code 84%", " : information: generating code 87%", " : information: generating code 90%", " : information: generating code 93%", " : information: generating code 95%", " : information: generating code 100%", " : information: code generated", "Result: 0 errors, 0 warnings, 868 ms elapsed, cpu='X64 Regular'"], "status": "PASS", "terminal_data": "C:\\Users\\ZHAO ZHU INFORMATION\\AppData\\Roaming\\MetaQuotes\\Terminal\\D0E8209F77C8CF37AD8BF550E51FF075"}, {"ea": "Phase2ExperimentalDemoExecutor", "ex5": "C:\\MT5PortableTier1BestEA\\MQL5\\Experts\\Phase2ExperimentalDemoExecutor.ex5", "log": "C:\\MT5PortableTier1BestEA\\MQL5\\Logs\\compile_Phase2ExperimentalDemoExecutor_a1_a2_920101_20260621.log", "log_tail": [" : information: generating code 72%", " : information: generating code 75%", " : information: generating code 78%", " : information: generating code 81%", " : information: generating code 84%", " : information: generating code 87%", " : information: generating code 90%", " : information: generating code 93%", " : information: generating code 95%", " : information: generating code 100%", " : information: code generated", "Result: 0 errors, 0 warnings, 1484 ms elapsed, cpu='X64 Regular'"], "status": "PASS", "terminal_data": "C:\\MT5PortableTier1BestEA"}, {"ea": "Account1DailyProfitFloorGuardian", "ex5": "C:\\MT5PortableTier1BestEA\\MQL5\\Experts\\Account1DailyProfitFloorGuardian.ex5", "log": "C:\\MT5PortableTier1BestEA\\MQL5\\Logs\\compile_Account1DailyProfitFloorGuardian_a1_a2_920101_20260621.log", "log_tail": [" : information: generating code 72%", " : information: generating code 75%", " : information: generating code 78%", " : information: generating code 81%", " : information: generating code 84%", " : information: generating code 87%", " : information: generating code 90%", " : information: generating code 93%", " : information: generating code 95%", " : information: generating code 100%", " : information: code generated", "Result: 0 errors, 0 warnings, 854 ms elapsed, cpu='X64 Regular'"], "status": "PASS", "terminal_data": "C:\\MT5PortableTier1BestEA"}] |

## Profile Backups

- A1: `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\_codex_quarantine\profile_backups\a1_a2_920101_maintenance_a1_20260628_153321`
- A2: `C:\MT5PortableTier1BestEA\_codex_quarantine\profile_backups\a1_a2_920101_maintenance_a2_20260628_153322`

## Changed Files

| Action | Path |
| --- | --- |
| write_chart | `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Profiles\Charts\Default\chart03.chr` |
| disabled_non_spec_broker_action | `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Profiles\Charts\Default\chart01.chr` |
| disabled_non_spec_broker_action | `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Profiles\Charts\Default\chart02.chr` |
| disabled_non_spec_broker_action | `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Profiles\Charts\Default\chart18.chr` |
| disabled_non_spec_broker_action | `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Profiles\Charts\Default\chart19.chr` |
| disabled_non_spec_broker_action | `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Profiles\Charts\Default\chart20.chr` |
| disabled_extra_phase2_executor | `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Profiles\Charts\Default\chart27.chr` |
| disabled_wr50_broker_action | `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Profiles\Charts\Default\chart21.chr` |
| updated_a1_guardian_daily_lock_loss | `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Profiles\Charts\Default\chart26.chr` |
| write_chart | `C:\MT5PortableTier1BestEA\MQL5\Profiles\Charts\Default\chart02.chr` |
| disabled_extra_phase2_executor | `C:\MT5PortableTier1BestEA\MQL5\Profiles\Charts\Default\chart04.chr` |
| write_chart | `C:\MT5PortableTier1BestEA\MQL5\Profiles\Charts\Default\chart03.chr` |

## After Runtime-Relevant Charts

### A1

| Chart | Symbol | Expert | Candidate | Account | Dry-run | Broker | Session | Smart trend | Max open | Cost | Spread | Guardian floor | Guardian loss | Halt file |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |
| chart03.chr | XAUUSD | `Phase2ExperimentalDemoExecutor` | `breakout_retest` | `1025742` | `false` | `true` | `12->15` | `true shadow=false D1=0.25 H1=0.35` | `1` | `0.30` | `75.0` | `next=` | `` | `` |
| chart24.chr | XAUUSD | `AccountEquityGuardianShadow` | `` | `` | `` | `` | `` | ` shadow= D1= H1=` | `` | `` | `` | `next=` | `` | `` |
| chart26.chr | XAUUSD | `Account1DailyProfitFloorGuardian` | `` | `` | `false` | `` | `` | ` shadow= D1= H1=` | `` | `` | `` | `50.0 next=100.0` | `true -100.0` | `experimental_demo_kill_switch.txt` |
| chart27.chr | XAUUSD | `Phase2ExperimentalDemoExecutor` | `breakout_retest` | `1025742` | `true` | `false` | `0->23` | ` shadow= D1= H1=` | `1` | `0.15` | `75.0` | `next=` | `` | `` |

### A2

| Chart | Symbol | Expert | Candidate | Account | Dry-run | Broker | Session | Smart trend | Max open | Cost | Spread | Guardian floor | Guardian loss | Halt file |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |
| chart01.chr | XAUUSD | `AccountEquityGuardianShadow` | `` | `` | `` | `` | `` | ` shadow= D1= H1=` | `` | `` | `` | `next=` | `` | `` |
| chart02.chr | XAUUSD | `Phase2ExperimentalDemoExecutor` | `breakout_retest` | `1033030` | `false` | `true` | `12->15` | `true shadow=false D1=0.25 H1=0.35` | `1` | `0.30` | `75.0` | `next=` | `` | `` |
| chart03.chr | XAUUSD | `Account1DailyProfitFloorGuardian` | `` | `` | `false` | `` | `` | ` shadow= D1= H1=` | `` | `` | `` | `50.0 next=100.0` | `true -100.0` | `tier1_bestea_kill_switch.txt` |
| chart04.chr | XAUUSD | `Phase2ExperimentalDemoExecutor` | `breakout_retest` | `1033030` | `true` | `false` | `0->23` | ` shadow= D1= H1=` | `1` | `0.15` | `75.0` | `next=` | `` | `` |

## Claude Verification Focus

- Confirm A1 now has exactly one broker-action XAU Phase2ExperimentalDemoExecutor breakout_retest chart for account 1025742.
- Confirm A1 EURUSD/GBPUSD standard executor and A1 repair/WR50 lanes are disarmed.
- Confirm A2 XAU Phase2ExperimentalDemoExecutor remains broker-action enabled and aligned to A1.
- Confirm A1 and A2 both have active daily profit/loss guardians using their account-specific halt files.
- Confirm A3 profile hashes did not change and A3 remains paused.
