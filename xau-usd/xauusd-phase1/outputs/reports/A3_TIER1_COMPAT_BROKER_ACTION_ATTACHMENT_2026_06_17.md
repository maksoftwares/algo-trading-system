# A3 Tier1 Compat Broker-Action Attachment

Overall status: `PASS`

Owner chat approval on 2026-06-17 to skip observer mode and start broker-action demo orders for A3 Tier1 compat.

Demo only; no canonical Phase 2 approval; no live trading or real-capital authorization.

## Attached Lane

| Field | Value |
| --- | --- |
| ea | `Account3BreakoutTier1CompatExecutor` |
| symbol | `XAUUSD` |
| timeframe | `M5` |
| account_login | `1033669` |
| magic | `933400` |
| comment | `A3_BREAKOUT_TIER1_COMPAT` |
| fixed_lot | `0.01` |
| dry_run | `false` |
| broker_action_allowed | `true` |
| session_gate_server_hours | `12-15` |
| xau_stop_floor_enabled | `true` |
| trend_guard_enabled | `false` |
| trend_shadow_only | `true` |

## Runtime Evidence

- Terminal: `C:\MT5PortableRepairLane\terminal64.exe`
- Profile backup: `C:\MT5PortableRepairLane\_codex_quarantine\profile_backups\default_profile_before_a3_tier1_compat_20260617_095353`
- Compile log: `C:\MT5PortableRepairLane\MQL5\Logs\compile_Account3BreakoutTier1CompatExecutor_broker_action_20260617.log`
- New chart: `C:\MT5PortableRepairLane\MQL5\Profiles\Charts\Default\chart04.chr`
- Local armed preset: `C:\MT5PortableRepairLane\MQL5\Presets\Account3BreakoutTier1CompatExecutor.armed_owner_20260617.set`
- Local armed preset SHA256: `eac7b1964e93d03a9cd5aba0af23ee7340ed8075eb868c8dacef68c2a3ad5c32`
- Startup log: `C:\MT5PortableRepairLane\MQL5\Files\a3_breakout_tier1_compat_startup.csv`
- Startup latest row: `2026.06.17 09:54:07,2026.06.17 09:54:03,2026.06.17 13:54:03,A3_BREAKOUT_TIER1_COMPAT_V1_ARMED_20260617,Capital.ComMena-Demo,1033669,XAUUSD,933400,A3_BREAKOUT_TIER1_COMPAT,1033669,false,true,0.01,1,0.1500,0.2000,0.3000,75.00,true,12,15,60,true,A3_KILL.txt,false,true,false,false,ATTACHED_A3_BREAKOUT_TIER1_COMPAT`

## Checks

| Check | Status | Evidence |
| --- | --- | --- |
| owner_chat_authorization_recorded | `PASS` | Broker-action approval recorded in A3_TIER1_COMPAT_BROKER_ACTION_OWNER_AUTHORIZATION_2026_06_17.md |
| compile_0_errors_0_warnings | `PASS` | C:\MT5PortableRepairLane\MQL5\Logs\compile_Account3BreakoutTier1CompatExecutor_broker_action_20260617.log |
| profile_backup_created | `PASS` | C:\MT5PortableRepairLane\_codex_quarantine\profile_backups\default_profile_before_a3_tier1_compat_20260617_095353 |
| preexisting_933400_chart_absent_or_reused | `PASS` | chart04.chr |
| preexisting_933400_broker_exposure_absent | `PASS` | {"matching_orders": [], "matching_positions": [], "matching_total": 0, "orders_total": 0, "positions_total": 0, "status": "PASS"} |
| local_armed_preset_written | `PASS` | C:\MT5PortableRepairLane\MQL5\Presets\Account3BreakoutTier1CompatExecutor.armed_owner_20260617.set |
| new_chart_added | `PASS` | C:\MT5PortableRepairLane\MQL5\Profiles\Charts\Default\chart04.chr |
| terminal_relaunched | `PASS` | C:\MT5PortableRepairLane\terminal64.exe |
| startup_log_present | `PASS` | C:\MT5PortableRepairLane\MQL5\Files\a3_breakout_tier1_compat_startup.csv |
| startup_log_armed | `PASS` | 2026.06.17 09:54:07,2026.06.17 09:54:03,2026.06.17 13:54:03,A3_BREAKOUT_TIER1_COMPAT_V1_ARMED_20260617,Capital.ComMena-Demo,1033669,XAUUSD,933400,A3_BREAKOUT_TIER1_COMPAT,1033669,false,true,0.01,1,0.1500,0.2000,0.3000,75.00,true,12,15,60,true,A3_KILL.txt,false,true,false,false,ATTACHED_A3_BREAKOUT_TIER1_COMPAT |
| existing_a3_lanes_preserved | `PASS` | Required magics 933200 and 933300 remain attached. |

## Before Charts

| Chart | Symbol | Expert | Magic | Broker Action | Dry Run | Lot | Run Id | Comment |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| chart01.chr | XAUUSD | Account3BreakoutPlainExecutor | 933200 | true | false | 0.01 | A3_BREAKOUT_PLAIN_V1_ARMED_20260616 | A3_BREAKOUT_PLAIN |
| chart02.chr | XAUUSD | Account3BreakoutImprovedExecutor | 933300 | true | false | 0.01 | A3_BREAKOUT_IMPROVED_V1_ARMED_20260616 | A3_BREAKOUT_IMPROVED |
| chart03.chr | XAUUSD | NO_EA |  |  |  |  |  |  |
| chart04.chr | XAUUSD | Account3BreakoutTier1CompatExecutor | 933400 | true | false | 0.01 | A3_BREAKOUT_TIER1_COMPAT_V1_ARMED_20260617 | A3_BREAKOUT_TIER1_COMPAT |

## After Charts

| Chart | Symbol | Expert | Magic | Broker Action | Dry Run | Lot | Run Id | Comment |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| chart01.chr | XAUUSD | Account3BreakoutPlainExecutor | 933200 | true | false | 0.01 | A3_BREAKOUT_PLAIN_V1_ARMED_20260616 | A3_BREAKOUT_PLAIN |
| chart02.chr | XAUUSD | Account3BreakoutImprovedExecutor | 933300 | true | false | 0.01 | A3_BREAKOUT_IMPROVED_V1_ARMED_20260616 | A3_BREAKOUT_IMPROVED |
| chart03.chr | XAUUSD | NO_EA |  |  |  |  |  |  |
| chart04.chr | XAUUSD | Account3BreakoutTier1CompatExecutor | 933400 | true | false | 0.01 | A3_BREAKOUT_TIER1_COMPAT_V1_ARMED_20260617 | A3_BREAKOUT_TIER1_COMPAT |
