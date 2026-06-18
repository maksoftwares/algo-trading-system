# A3 Soft Retest V2 Broker-Action Attachment

Overall status: `PASS`

Owner chat approval on 2026-06-18 to attach A3 soft-retest V2 for broker-action demo orders after compile/exposure/startup checks.

Demo only; A3 account 1033669 only; XAUUSD only; no real-capital or live-server authorization.

## Attached Lane

| Field | Value |
| --- | --- |
| ea | `Account3SoftRetestExecutor` |
| symbol | `XAUUSD` |
| timeframe | `M5` |
| account_login | `1033669` |
| magic | `933500` |
| comment | `A3_SOFT_RETEST_V2` |
| fixed_lot | `0.01` |
| dry_run | `false` |
| broker_action_allowed | `true` |
| session_gate_server_hours | `0-23` |
| xau_stop_floor_enabled | `true` |
| trend_guard_enabled | `false` |
| trend_shadow_only | `false` |

## Candidate

| Field | Value |
| --- | --- |
| candidate_id | `A3_SQ_SOFT_RETEST_W15_B45_C60_RCM05_V2` |
| source_doc | `xau-usd/xauusd-phase1/docs/A3_SIGNAL_QUALITY_V2_SOFT_RETEST_W15_B45_C60_RCM05_2026_06_18.md` |
| owner_packet | `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\A3_SOFT_RETEST_BROKER_ACTION_OWNER_AUTHORIZATION_2026_06_18.md` |

## Runtime Evidence

- Terminal: `C:\MT5PortableRepairLane\terminal64.exe`
- Profile backup: `C:\MT5PortableRepairLane\_codex_quarantine\profile_backups\default_profile_before_a3_tier1_compat_20260618_151142`
- Compile log: `C:\MT5PortableRepairLane\MQL5\Logs\compile_Account3SoftRetestExecutor_broker_action_20260617.log`
- New chart: `C:\MT5PortableRepairLane\MQL5\Profiles\Charts\Default\chart06.chr`
- Local armed preset: `C:\MT5PortableRepairLane\MQL5\Presets\Account3SoftRetestExecutor.armed_owner_20260618.set`
- Local armed preset SHA256: `c98c81412bf61e0bca417a56360e8ab3e9b0ec3b5fc14d9e7710b830825a99a4`
- Startup log: `C:\MT5PortableRepairLane\MQL5\Files\a3_soft_retest_v2_startup.csv`
- Startup latest row: `2026.06.18 15:11:46,2026.06.18 15:11:45,2026.06.18 19:11:45,A3_SQ_SOFT_RETEST_W15_B45_C60_RCM05_V2_ARMED_20260618,Capital.ComMena-Demo,1033669,XAUUSD,933500,A3_SOFT_RETEST_V2,1033669,false,true,0.01,1,0.1500,0.2000,0.3000,75.00,false,0,23,60,true,A3_EXECUTION_KILL.txt,A3_FULL_STOP.txt,false,false,true,15,0.45,0.60,0.05,false,false,ATTACHED_A3_SOFT_RETEST_V2`

## Checks

| Check | Status | Evidence |
| --- | --- | --- |
| owner_chat_authorization_recorded | `PASS` | Broker-action approval recorded in A3_SOFT_RETEST_BROKER_ACTION_OWNER_AUTHORIZATION_2026_06_18.md |
| compile_0_errors_0_warnings | `PASS` | C:\MT5PortableRepairLane\MQL5\Logs\compile_Account3SoftRetestExecutor_broker_action_20260617.log |
| profile_backup_created | `PASS` | C:\MT5PortableRepairLane\_codex_quarantine\profile_backups\default_profile_before_a3_tier1_compat_20260618_151142 |
| preexisting_933500_chart_absent_or_reused | `PASS` | none |
| preexisting_a3_broker_exposure_zero | `PASS` | {"checked_magics": [933200, 933300, 933400, 933500], "matching_orders": [], "matching_positions": [], "matching_total": 0, "orders_total": 0, "positions_total": 0, "status": "PASS"} |
| preexisting_933500_broker_exposure_absent | `PASS` | {"matching_orders": [], "matching_positions": [], "matching_total": 0, "orders_total": 0, "positions_total": 0, "status": "PASS"} |
| local_armed_preset_written | `PASS` | C:\MT5PortableRepairLane\MQL5\Presets\Account3SoftRetestExecutor.armed_owner_20260618.set |
| new_chart_added | `PASS` | C:\MT5PortableRepairLane\MQL5\Profiles\Charts\Default\chart06.chr |
| terminal_relaunched | `PASS` | C:\MT5PortableRepairLane\terminal64.exe |
| startup_log_present | `PASS` | C:\MT5PortableRepairLane\MQL5\Files\a3_soft_retest_v2_startup.csv |
| startup_log_armed | `PASS` | 2026.06.18 15:11:46,2026.06.18 15:11:45,2026.06.18 19:11:45,A3_SQ_SOFT_RETEST_W15_B45_C60_RCM05_V2_ARMED_20260618,Capital.ComMena-Demo,1033669,XAUUSD,933500,A3_SOFT_RETEST_V2,1033669,false,true,0.01,1,0.1500,0.2000,0.3000,75.00,false,0,23,60,true,A3_EXECUTION_KILL.txt,A3_FULL_STOP.txt,false,false,true,15,0.45,0.60,0.05,false,false,ATTACHED_A3_SOFT_RETEST_V2 |
| profile_inventory_checked | `PASS` | Soft-retest attach does not require legacy A3 lane preservation. |

## Before Charts

| Chart | Symbol | Expert | Magic | Broker Action | Dry Run | Lot | Run Id | Comment |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| chart01.chr | XAUUSD | Account3BreakoutPlainExecutor | 933200 | false | true | 0.01 | A3_BREAKOUT_PLAIN_V1_STOPPED_20260618 | A3_BREAKOUT_PLAIN |
| chart02.chr | XAUUSD | Account3BreakoutImprovedExecutor | 933300 | false | true | 0.01 | A3_BREAKOUT_IMPROVED_V1_PAUSED_20260618 | A3_BREAKOUT_IMPROVED |
| chart03.chr | XAUUSD | NO_EA |  |  |  |  |  |  |
| chart04.chr | XAUUSD | Account3BreakoutTier1CompatExecutor | 933400 | false | true | 0.01 | A3_BREAKOUT_TIER1_COMPAT_V1_PAUSED_20260618 | A3_BREAKOUT_TIER1_COMPAT |
| chart05.chr | XAUUSD | Account3ProfitLockExitManager |  |  | true |  | A3_PROFIT_LOCK_EXIT_MANAGER_V1_DRYRUN_PAUSED_20260618 |  |

## After Charts

| Chart | Symbol | Expert | Magic | Broker Action | Dry Run | Lot | Run Id | Comment |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| chart01.chr | XAUUSD | Account3BreakoutPlainExecutor | 933200 | false | true | 0.01 | A3_BREAKOUT_PLAIN_V1_STOPPED_20260618 | A3_BREAKOUT_PLAIN |
| chart02.chr | XAUUSD | Account3BreakoutImprovedExecutor | 933300 | false | true | 0.01 | A3_BREAKOUT_IMPROVED_V1_PAUSED_20260618 | A3_BREAKOUT_IMPROVED |
| chart03.chr | XAUUSD | NO_EA |  |  |  |  |  |  |
| chart04.chr | XAUUSD | Account3BreakoutTier1CompatExecutor | 933400 | false | true | 0.01 | A3_BREAKOUT_TIER1_COMPAT_V1_PAUSED_20260618 | A3_BREAKOUT_TIER1_COMPAT |
| chart05.chr | XAUUSD | Account3ProfitLockExitManager |  |  | true |  | A3_PROFIT_LOCK_EXIT_MANAGER_V1_DRYRUN_PAUSED_20260618 |  |
| chart06.chr | XAUUSD | Account3SoftRetestExecutor | 933500 | true | false | 0.01 | A3_SQ_SOFT_RETEST_W15_B45_C60_RCM05_V2_ARMED_20260618 | A3_SOFT_RETEST_V2 |

