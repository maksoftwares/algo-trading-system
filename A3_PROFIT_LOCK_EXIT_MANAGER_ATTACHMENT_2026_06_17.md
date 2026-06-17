# A3 Profit-Lock Exit Manager Attachment

Overall status: `PASS`

Owner work order CODEX_WORK_ORDER_A3_PROFIT_LOCK_EXIT_MANAGER_LIVE_2026_06_17.md; Step0 replay gate passed before arming.

A3 demo account 1033669 only; XAUUSD only; separate exit manager; no entry EA/kernel edits; SLTP modifications only.

## Step0 Gate

- Duplicate-hidden path-covered rows: `252`
- Control PnL: `-647.36 AED`
- Replay PnL: `-424.50 AED`
- Delta: `222.86 AED`
- Best-day-removed delta: `63.37 AED`

## Armed Manager

| Field | Value |
| --- | --- |
| ea | `Account3ProfitLockExitManager` |
| symbol | `XAUUSD` |
| timeframe | `M5` |
| account_login | `1033669` |
| managed_magics | `933200,933400` |
| excluded_magic | `933300` |
| dry_run | `false` |
| manage_action_allowed | `true` |
| primary_trigger_r | `1.25` |
| primary_lock_r | `0.80` |
| secondary_enabled | `false` |
| tertiary_enabled | `false` |

## Runtime Evidence

- Terminal: `C:\MT5PortableRepairLane\terminal64.exe`
- Profile backup: `C:\MT5PortableRepairLane\_codex_quarantine\profile_backups\default_profile_before_a3_profit_lock_20260617_210518`
- Compile log: `C:\MT5PortableRepairLane\MQL5\Logs\compile_Account3ProfitLockExitManager_20260618.log`
- New chart: `C:\MT5PortableRepairLane\MQL5\Profiles\Charts\Default\chart05.chr`
- Local armed preset: `C:\MT5PortableRepairLane\MQL5\Presets\Account3ProfitLockExitManager.armed_owner_20260618.set`
- Local armed preset SHA256: `4edda65ff60b454953a7460c03648fb447763d763326592fe54e85a3a1742d15`
- Startup log: `C:\MT5PortableRepairLane\MQL5\Files\a3_profit_lock_exit_manager_startup.csv`
- Startup latest row: `2026.06.17 21:05:22,A3_PROFIT_LOCK_EXIT_MANAGER_V1_ARMED_20260618,Capital.ComMena-Demo,1033669,XAUUSD,XAUUSD,"933200,933400",false,true,A3_KILL.txt,true,1.25,0.80,false,false,ATTACHED_A3_PROFIT_LOCK_EXIT_MANAGER,OK`

## Checks

| Check | Status | Evidence |
| --- | --- | --- |
| step0_replay_gate_pass | `PASS` | status=PASS; delta=222.86 AED; best_day_removed=63.37 AED; rows=252 |
| compile_0_errors_0_warnings | `PASS` | C:\MT5PortableRepairLane\MQL5\Logs\compile_Account3ProfitLockExitManager_20260618.log |
| profile_backup_created | `PASS` | C:\MT5PortableRepairLane\_codex_quarantine\profile_backups\default_profile_before_a3_profit_lock_20260617_210518 |
| local_armed_preset_written | `PASS` | C:\MT5PortableRepairLane\MQL5\Presets\Account3ProfitLockExitManager.armed_owner_20260618.set |
| new_chart_added | `PASS` | C:\MT5PortableRepairLane\MQL5\Profiles\Charts\Default\chart05.chr |
| manager_defaults_armed_only_in_local_preset | `PASS` | DryRunOnly=false and ManageActionAllowed=true only in local owner preset/chart. |
| managed_magic_allowlist_excludes_933300 | `PASS` | 933200,933400 |
| existing_a3_lanes_preserved | `PASS` | Required entry magics 933200, 933300, and 933400 remain attached. |
| terminal_relaunched | `PASS` | C:\MT5PortableRepairLane\terminal64.exe |
| startup_log_present | `PASS` | C:\MT5PortableRepairLane\MQL5\Files\a3_profit_lock_exit_manager_startup.csv |
| startup_log_armed | `PASS` | 2026.06.17 21:05:22,A3_PROFIT_LOCK_EXIT_MANAGER_V1_ARMED_20260618,Capital.ComMena-Demo,1033669,XAUUSD,XAUUSD,"933200,933400",false,true,A3_KILL.txt,true,1.25,0.80,false,false,ATTACHED_A3_PROFIT_LOCK_EXIT_MANAGER,OK |
| runtime_account_1033669_demo | `PASS` | {"login": 1033669, "server": "Capital.ComMena-Demo", "trade_allowed": true} |
| kill_switch_absent_at_attach | `PASS` | C:\MT5PortableRepairLane\MQL5\Files\A3_KILL.txt |

## Open XAUUSD Positions After Attach

| Ticket | Magic | Type | Volume | Open | SL | TP | Profit | Comment |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 4132280 | 933200 | 1 | 0.01 | 4271.78 | 4306.99 | 4217.99 | 50.01 | A3_BREAKOUT_PLAIN |
| 4136095 | 933300 | 1 | 0.01 | 4258.32 | 4270.92 | 4239.30 | 0.59 | A3_BREAKOUT_IMPROVED |

## Before Charts

| Chart | Symbol | Expert | Magic | Managed Magics | Manage Action | Broker Action | Dry Run | Run Id | Comment |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: | --- | --- |
| chart01.chr | XAUUSD | Account3BreakoutPlainExecutor | 933200 |  |  | true | false | A3_BREAKOUT_PLAIN_V1_ARMED_20260616 | A3_BREAKOUT_PLAIN |
| chart02.chr | XAUUSD | Account3BreakoutImprovedExecutor | 933300 |  |  | true | false | A3_BREAKOUT_IMPROVED_V1_ARMED_20260616 | A3_BREAKOUT_IMPROVED |
| chart03.chr | XAUUSD | NO_EA |  |  |  |  |  |  |  |
| chart04.chr | XAUUSD | Account3BreakoutTier1CompatExecutor | 933400 |  |  | true | false | A3_BREAKOUT_TIER1_COMPAT_V1_ARMED_20260617 | A3_BREAKOUT_TIER1_COMPAT |

## After Charts

| Chart | Symbol | Expert | Magic | Managed Magics | Manage Action | Broker Action | Dry Run | Run Id | Comment |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: | --- | --- |
| chart01.chr | XAUUSD | Account3BreakoutPlainExecutor | 933200 |  |  | true | false | A3_BREAKOUT_PLAIN_V1_ARMED_20260616 | A3_BREAKOUT_PLAIN |
| chart02.chr | XAUUSD | Account3BreakoutImprovedExecutor | 933300 |  |  | true | false | A3_BREAKOUT_IMPROVED_V1_ARMED_20260616 | A3_BREAKOUT_IMPROVED |
| chart03.chr | XAUUSD | NO_EA |  |  |  |  |  |  |  |
| chart04.chr | XAUUSD | Account3BreakoutTier1CompatExecutor | 933400 |  |  | true | false | A3_BREAKOUT_TIER1_COMPAT_V1_ARMED_20260617 | A3_BREAKOUT_TIER1_COMPAT |
| chart05.chr | XAUUSD | Account3ProfitLockExitManager |  | 933200,933400 | true |  | false | A3_PROFIT_LOCK_EXIT_MANAGER_V1_ARMED_20260618 |  |
