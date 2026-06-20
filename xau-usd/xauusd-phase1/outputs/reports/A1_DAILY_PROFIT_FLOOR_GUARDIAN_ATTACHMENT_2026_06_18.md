# A1 Daily Profit-Floor Guardian Attachment - 2026-06-18

Status: `PASS`

Owner-authorized A1 live-demo close-only daily +100 AED profit-floor guardian. Demo only; no canonical Phase 2/3 change; no live/real capital.

## Boundary

- Account: `1025742 / Capital.ComMena-Demo`
- A2 touched: `false`
- A3 touched: `false`
- Entry EAs edited: `false`
- Opens trades: `false`
- Close-only broker action: `true`
- Daily loss stop enabled: `false`

## Runtime

- EA: `Account1DailyProfitFloorGuardian`
- Chart: `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Profiles\Charts\Default\chart26.chr`
- Source deployed: `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts\Account1DailyProfitFloorGuardian.mq5`
- Compile log: `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Logs\compile_Account1DailyProfitFloorGuardian_20260618.log`
- Local armed preset: `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Presets\Account1DailyProfitFloorGuardian.armed_owner_20260618.set`
- Runtime dry-run: `false`
- Runtime close action allowed: `true`
- Daily floor: `100.00 AED`
- Entry halt file: `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files\experimental_demo_kill_switch.txt`

## Entry-Halt Verification

Phase2ExperimentalDemoExecutor checks KillSwitchActive() inside TradingGuardsPass() before sending orders, so the halt file blocks future entries without editing entry EAs.

## Checks

| Check | Status | Evidence |
|---|---|---|
| a1_account_login | `PASS` | {'login': 1025742, 'server': 'Capital.ComMena-Demo', 'balance': 1613.48, 'equity': 1617.34, 'trade_allowed': True, 'positions_total': 1, 'orders_total': 0, 'position_tickets': [4146010]} |
| profile_backup_created | `PASS` | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\_codex_quarantine\profile_backups\default_profile_before_a1_profit_floor_guardian_20260618_105858 |
| chart_appended | `PASS` | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Profiles\Charts\Default\chart26.chr |
| compile_0_errors_0_warnings | `PASS` | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Logs\compile_Account1DailyProfitFloorGuardian_20260618.log |
| startup_log_attached | `PASS` | ,state_file,event_log,daily_summary_log,startup_status,detail
2026.06.18 10:59:05,2026.06.18 10:59:01,2026.06.18 14:59:01,A1_DAILY_PROFIT_FLOOR_GUARDIAN_V1_ARMED_20260618,1025742,Capital.ComMena-Demo,false,true,true,100.00,false,-150.00,A1_DAILY_PROFIT_FLOOR_GUARDIAN_KILL.txt,experimental_demo_kill_switch.txt,A1_DAILY_PROFIT_FLOOR_GUARDIAN_STATE.txt,A1_DAILY_PROFIT_FLOOR_GUARDIAN_EVENTS.csv,A1_DAILY_PROFIT_FLOOR_GUARDIAN_DAILY_SUMMARY.csv,ATTACHED_A1_DAILY_PROFIT_FLOOR_GUARDIAN,state_initialized |
| guardian_does_not_open_on_attach | `PASS` | before={'login': 1025742, 'server': 'Capital.ComMena-Demo', 'balance': 1613.48, 'equity': 1617.34, 'trade_allowed': True, 'positions_total': 1, 'orders_total': 0, 'position_tickets': [4146010]}; after={'login': 1025742, 'server': 'Capital.ComMena-Demo', 'balance': 1613.48, 'equity': 1617.3, 'trade_allowed': True, 'positions_total': 1, 'orders_total': 0, 'position_tickets': [4146010]} |

## Startup Tail

```text
timestamp_broker,timestamp_utc,timestamp_dubai,run_id,account_login,server,dry_run,close_action_allowed,owner_token_present,daily_floor_aed,daily_loss_stop_enabled,daily_loss_stop_aed,guardian_kill_switch_file,entry_halt_file,state_file,event_log,daily_summary_log,startup_status,detail
2026.06.18 10:59:05,2026.06.18 10:59:01,2026.06.18 14:59:01,A1_DAILY_PROFIT_FLOOR_GUARDIAN_V1_ARMED_20260618,1025742,Capital.ComMena-Demo,false,true,true,100.00,false,-150.00,A1_DAILY_PROFIT_FLOOR_GUARDIAN_KILL.txt,experimental_demo_kill_switch.txt,A1_DAILY_PROFIT_FLOOR_GUARDIAN_STATE.txt,A1_DAILY_PROFIT_FLOOR_GUARDIAN_EVENTS.csv,A1_DAILY_PROFIT_FLOOR_GUARDIAN_DAILY_SUMMARY.csv,ATTACHED_A1_DAILY_PROFIT_FLOOR_GUARDIAN,state_initialized
```

## Event Tail

```text
timestamp_broker,timestamp_utc,timestamp_dubai,run_id,account_login,server,event,reason,dubai_date,day_start_equity,equity,day_pnl,peak_day_pnl,armed,locked,positions_total,positions_closed_today,close_failures_today,ticket,symbol,direction,volume,price,retcode,retcode_description,dry_run,close_action_allowed
2026.06.18 10:59:05,2026.06.18 10:59:01,2026.06.18 14:59:01,A1_DAILY_PROFIT_FLOOR_GUARDIAN_V1_ARMED_20260618,1025742,Capital.ComMena-Demo,DAY_RESET,dubai_day_start,2026.06.18,1617.22,1617.22,0.00,0.00,false,false,1,0,0,0,,,0.00,0.00000,0,,false,true
```

## State Tail

```text
peak_day_pnl=0.04
armed=false
locked=false
armed_time=
trigger_time=
trigger_reason=
positions_closed_today=0
close_failures_today=0
locked_equity=0.00
locked_day_pnl=0.00
```

## Owner-Acknowledged Expectations

- This caps bleed; it does not make A1 profitable by itself.
- The fixed +100 AED floor can clip recovery days.
- A trigger closes protected breakout-core positions too.
- Locked result is approximately +100 AED minus closing slippage.
