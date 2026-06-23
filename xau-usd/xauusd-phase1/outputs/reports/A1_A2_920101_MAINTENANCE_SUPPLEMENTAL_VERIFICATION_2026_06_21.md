# A1/A2 920101 Maintenance Supplemental Verification - 2026-06-21

Status: `PASS_WITH_ORDER_LOG_PENDING`

Created UTC: `2026-06-22T20:54:44+00:00`

This is a read-only verification report. It refreshes the stale runtime chart inventory and surfaces startup identity proof after the A1/A2 920101 maintenance. It does not change MT5 runtime state.

## Checks

| Check | Status | Detail |
|---|---|---|
| a1_chart03_920101_active | `PASS` | A1 chart03.chr XAUUSD Phase2ExperimentalDemoExecutor BROKER_ACTION_ENABLED magic=920101 |
| a2_chart02_920101_active | `PASS` | A2 chart02.chr XAUUSD Phase2ExperimentalDemoExecutor BROKER_ACTION_ENABLED magic=920101 |
| a1_non_spec_lanes_disarmed | `PASS` | A1 chart01.chr EURUSD NO_EA NO_EA magic=; A1 chart02.chr GBPUSD NO_EA NO_EA magic=; A1 chart18.chr XAUUSD NO_EA NO_EA magic=; A1 chart19.chr XAUUSD NO_EA NO_EA magic=; A1 chart20.chr EURUSD NO_EA NO_EA magic= |
| a1_wr50_disarmed | `PASS` | A1 chart21.chr XAUUSD NO_EA NO_EA magic= |
| a1_guardian_active | `PASS` | A1 chart26.chr XAUUSD Account1DailyProfitFloorGuardian GUARDIAN_CLOSE_ACTION_ENABLED magic= |
| a2_guardian_active | `PASS` | A2 chart03.chr XAUUSD Account1DailyProfitFloorGuardian GUARDIAN_CLOSE_ACTION_ENABLED magic= |
| a3_no_broker_action_enabled | `PASS` | A3 has no broker-action enabled rows in inspected profile. |
| a1_startup_mentions_920101 | `PASS` | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files\a1_920101_evening_startup_log.csv |
| a2_startup_mentions_920101 | `PASS` | C:\MT5PortableTier1BestEA\MQL5\Files\a2_920101_evening_startup_log.csv |
| a1_guardian_startup_active | `PASS` | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files\A1_DAILY_PROFIT_LOSS_GUARDIAN_STARTUP.csv |
| a2_guardian_startup_active | `PASS` | C:\MT5PortableTier1BestEA\MQL5\Files\A2_DAILY_PROFIT_LOSS_GUARDIAN_STARTUP.csv |

## Key Runtime Inventory

Full refreshed inventory CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\RUNTIME_CHART_INVENTORY_FORENSIC_2026_06_21.csv`

| Lane | Chart | Symbol | Expert | State | Derived magic | Dry-run | Broker action | Demo trading | Session | Account |
|---|---|---|---|---|---:|---|---|---|---|---|
| A1 | chart01.chr | EURUSD | `NO_EA` | `NO_EA` | `` | `` | `` | `` | `->` | `` |
| A1 | chart02.chr | GBPUSD | `NO_EA` | `NO_EA` | `` | `` | `` | `` | `->` | `` |
| A1 | chart03.chr | XAUUSD | `Phase2ExperimentalDemoExecutor` | `BROKER_ACTION_ENABLED` | `920101` | `false` | `true` | `` | `12->15` | `1025742` |
| A1 | chart18.chr | XAUUSD | `NO_EA` | `NO_EA` | `` | `` | `` | `` | `->` | `` |
| A1 | chart19.chr | XAUUSD | `NO_EA` | `NO_EA` | `` | `` | `` | `` | `->` | `` |
| A1 | chart20.chr | EURUSD | `NO_EA` | `NO_EA` | `` | `` | `` | `` | `->` | `` |
| A1 | chart21.chr | XAUUSD | `NO_EA` | `NO_EA` | `` | `` | `` | `` | `->` | `` |
| A1 | chart26.chr | XAUUSD | `Account1DailyProfitFloorGuardian` | `GUARDIAN_CLOSE_ACTION_ENABLED` | `` | `false` | `` | `` | `->` | `` |
| A2 | chart02.chr | XAUUSD | `Phase2ExperimentalDemoExecutor` | `BROKER_ACTION_ENABLED` | `920101` | `false` | `true` | `` | `12->15` | `1033030` |
| A2 | chart03.chr | XAUUSD | `Account1DailyProfitFloorGuardian` | `GUARDIAN_CLOSE_ACTION_ENABLED` | `` | `false` | `` | `` | `->` | `` |

## Derived Magic Proof

`920101` is not a static chart input. It is derived at runtime by `Phase2ExperimentalDemoExecutor.mq5`:

```text
920000 + CandidateMagicOffset(InpCandidate) * 10 + SymbolMagicOffset(_Symbol)
breakout_retest offset = 10
XAUUSD offset = 1
920000 + 10 * 10 + 1 = 920101
```

Source: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\mt5\Experts\Phase2ExperimentalDemoExecutor.mq5`

- Source formula present: `True`
- Breakout offset present: `True`
- XAUUSD offset present: `True`

## Startup Evidence

### A1_920101

Path: `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files\a1_920101_evening_startup_log.csv`

```text
2026.06.22 11:13:02,2026.06.22 11:12:58,2026.06.22 15:12:58,A1_XAU_920101_EVENING_FORWARD_V0_20260621,Capital.ComMena-Demo,XAUUSD,breakout_retest,EXPERIMENTAL_QUARANTINE_REVIEW_ONLY,COST_SUSPENDED_CANONICAL,XAUUSD,1025742,1025742,breakout_retest,false,true,true,true,true,0,UNLIMITED,experimental_demo_kill_switch.txt,REMOVED_REASON_9
2026.06.22 11:13:22,2026.06.22 11:13:18,2026.06.22 15:13:18,A1_XAU_920101_EVENING_FORWARD_V0_20260621,Capital.ComMena-Demo,XAUUSD,breakout_retest,EXPERIMENTAL_QUARANTINE_REVIEW_ONLY,COST_SUSPENDED_CANONICAL,XAUUSD,1025742,1025742,breakout_retest,false,true,true,true,true,0,UNLIMITED,0.3000,75.00,experimental_demo_kill_switch.txt,GV_MUTEX_NAMESPACE_SELF_TEST_PASS name=FAMMUX_SELFTEST_1025742_XAUUSD_920101_20260622_111318
2026.06.22 11:13:22,2026.06.22 11:13:18,2026.06.22 15:13:18,A1_XAU_920101_EVENING_FORWARD_V0_20260621,Capital.ComMena-Demo,XAUUSD,breakout_retest,EXPERIMENTAL_QUARANTINE_REVIEW_ONLY,COST_SUSPENDED_CANONICAL,XAUUSD,1025742,1025742,breakout_retest,false,true,true,true,true,0,UNLIMITED,0.3000,75.00,experimental_demo_kill_switch.txt,ATTACHED_DEMO_EXECUTOR_ENABLED
2026.06.22 11:18:23,2026.06.22 11:18:19,2026.06.22 15:18:19,A1_XAU_920101_EVENING_FORWARD_V0_20260621,Capital.ComMena-Demo,XAUUSD,breakout_retest,EXPERIMENTAL_QUARANTINE_REVIEW_ONLY,COST_SUSPENDED_CANONICAL,XAUUSD,1025742,1025742,breakout_retest,false,true,true,true,true,0,UNLIMITED,experimental_demo_kill_switch.txt,REMOVED_REASON_9
2026.06.22 20:52:08,2026.06.22 20:52:02,2026.06.23 00:52:02,A1_XAU_920101_EVENING_FORWARD_V0_20260621,Capital.ComMena-Demo,XAUUSD,breakout_retest,EXPERIMENTAL_QUARANTINE_REVIEW_ONLY,COST_SUSPENDED_CANONICAL,XAUUSD,1025742,1025742,breakout_retest,false,true,true,true,true,0,UNLIMITED,0.3000,75.00,experimental_demo_kill_switch.txt,GV_MUTEX_NAMESPACE_SELF_TEST_PASS name=FAMMUX_SELFTEST_1025742_XAUUSD_920101_20260622_205202
2026.06.22 20:52:08,2026.06.22 20:52:02,2026.06.23 00:52:02,A1_XAU_920101_EVENING_FORWARD_V0_20260621,Capital.ComMena-Demo,XAUUSD,breakout_retest,EXPERIMENTAL_QUARANTINE_REVIEW_ONLY,COST_SUSPENDED_CANONICAL,XAUUSD,1025742,1025742,breakout_retest,false,true,true,true,true,0,UNLIMITED,0.3000,75.00,experimental_demo_kill_switch.txt,ATTACHED_DEMO_EXECUTOR_ENABLED
```
### A2_920101

Path: `C:\MT5PortableTier1BestEA\MQL5\Files\a2_920101_evening_startup_log.csv`

```text
2026.06.22 11:15:16,2026.06.22 11:15:12,2026.06.22 15:15:12,A2_XAU_920101_EVENING_FORWARD_V0_20260621,Capital.ComMena-Demo,XAUUSD,breakout_retest,EXPERIMENTAL_QUARANTINE_REVIEW_ONLY,COST_SUSPENDED_CANONICAL,XAUUSD,1033030,1033030,breakout_retest,false,true,true,true,true,0,UNLIMITED,tier1_bestea_kill_switch.txt,REMOVED_REASON_9
2026.06.22 11:15:25,2026.06.22 11:15:21,2026.06.22 15:15:21,A2_XAU_920101_EVENING_FORWARD_V0_20260621,Capital.ComMena-Demo,XAUUSD,breakout_retest,EXPERIMENTAL_QUARANTINE_REVIEW_ONLY,COST_SUSPENDED_CANONICAL,XAUUSD,1033030,1033030,breakout_retest,false,true,true,true,true,0,UNLIMITED,0.3000,75.00,tier1_bestea_kill_switch.txt,GV_MUTEX_NAMESPACE_SELF_TEST_PASS name=FAMMUX_SELFTEST_1033030_XAUUSD_920101_20260622_111521
2026.06.22 11:15:25,2026.06.22 11:15:21,2026.06.22 15:15:21,A2_XAU_920101_EVENING_FORWARD_V0_20260621,Capital.ComMena-Demo,XAUUSD,breakout_retest,EXPERIMENTAL_QUARANTINE_REVIEW_ONLY,COST_SUSPENDED_CANONICAL,XAUUSD,1033030,1033030,breakout_retest,false,true,true,true,true,0,UNLIMITED,0.3000,75.00,tier1_bestea_kill_switch.txt,ATTACHED_DEMO_EXECUTOR_ENABLED
2026.06.22 11:20:33,2026.06.22 11:20:28,2026.06.22 15:20:28,A2_XAU_920101_EVENING_FORWARD_V0_20260621,Capital.ComMena-Demo,XAUUSD,breakout_retest,EXPERIMENTAL_QUARANTINE_REVIEW_ONLY,COST_SUSPENDED_CANONICAL,XAUUSD,1033030,1033030,breakout_retest,false,true,true,true,true,0,UNLIMITED,tier1_bestea_kill_switch.txt,REMOVED_REASON_9
2026.06.22 20:52:08,2026.06.22 20:52:02,2026.06.23 00:52:02,A2_XAU_920101_EVENING_FORWARD_V0_20260621,Capital.ComMena-Demo,XAUUSD,breakout_retest,EXPERIMENTAL_QUARANTINE_REVIEW_ONLY,COST_SUSPENDED_CANONICAL,XAUUSD,1033030,1033030,breakout_retest,false,true,true,true,true,0,UNLIMITED,0.3000,75.00,tier1_bestea_kill_switch.txt,GV_MUTEX_NAMESPACE_SELF_TEST_PASS name=FAMMUX_SELFTEST_1033030_XAUUSD_920101_20260622_205202
2026.06.22 20:52:08,2026.06.22 20:52:02,2026.06.23 00:52:02,A2_XAU_920101_EVENING_FORWARD_V0_20260621,Capital.ComMena-Demo,XAUUSD,breakout_retest,EXPERIMENTAL_QUARANTINE_REVIEW_ONLY,COST_SUSPENDED_CANONICAL,XAUUSD,1033030,1033030,breakout_retest,false,true,true,true,true,0,UNLIMITED,0.3000,75.00,tier1_bestea_kill_switch.txt,ATTACHED_DEMO_EXECUTOR_ENABLED
```
### A1_guardian

Path: `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files\A1_DAILY_PROFIT_LOSS_GUARDIAN_STARTUP.csv`

```text
2026.06.22 11:18:23,2026.06.22 11:18:19,2026.06.22 15:18:19,A1_DAILY_PROFIT_LOSS_GUARDIAN_V1_ARMED_20260621,1025742,Capital.ComMena-Demo,false,true,true,100.00,true,-100.00,A1_DAILY_PROFIT_LOSS_GUARDIAN_KILL.txt,experimental_demo_kill_switch.txt,A1_DAILY_PROFIT_LOSS_GUARDIAN_STATE.txt,A1_DAILY_PROFIT_LOSS_GUARDIAN_EVENTS.csv,A1_DAILY_PROFIT_LOSS_GUARDIAN_DAILY_SUMMARY.csv,REMOVED_REASON_9,guardian_deinit
2026.06.22 11:18:40,2026.06.22 11:18:36,2026.06.22 15:18:36,A1_DAILY_PROFIT_LOSS_GUARDIAN_V1_ARMED_20260621,1025742,Capital.ComMena-Demo,false,true,true,100.00,true,-100.00,A1_DAILY_PROFIT_LOSS_GUARDIAN_KILL.txt,experimental_demo_kill_switch.txt,A1_DAILY_PROFIT_LOSS_GUARDIAN_STATE.txt,A1_DAILY_PROFIT_LOSS_GUARDIAN_EVENTS.csv,A1_DAILY_PROFIT_LOSS_GUARDIAN_DAILY_SUMMARY.csv,ATTACHED_A1_DAILY_PROFIT_FLOOR_GUARDIAN,state_restored
2026.06.22 11:29:16,2026.06.22 11:29:12,2026.06.22 15:29:12,A1_DAILY_PROFIT_LOSS_GUARDIAN_V1_ARMED_20260621,1025742,Capital.ComMena-Demo,false,true,true,100.00,true,-100.00,A1_DAILY_PROFIT_LOSS_GUARDIAN_KILL.txt,experimental_demo_kill_switch.txt,A1_DAILY_PROFIT_LOSS_GUARDIAN_STATE.txt,A1_DAILY_PROFIT_LOSS_GUARDIAN_EVENTS.csv,A1_DAILY_PROFIT_LOSS_GUARDIAN_DAILY_SUMMARY.csv,REMOVED_REASON_9,guardian_deinit
2026.06.22 11:29:34,2026.06.22 11:29:29,2026.06.22 15:29:29,A1_DAILY_PROFIT_LOSS_GUARDIAN_V1_ARMED_20260621,1025742,Capital.ComMena-Demo,false,true,true,100.00,true,-100.00,A1_DAILY_PROFIT_LOSS_GUARDIAN_KILL.txt,experimental_demo_kill_switch.txt,A1_DAILY_PROFIT_LOSS_GUARDIAN_STATE.txt,A1_DAILY_PROFIT_LOSS_GUARDIAN_EVENTS.csv,A1_DAILY_PROFIT_LOSS_GUARDIAN_DAILY_SUMMARY.csv,ATTACHED_A1_DAILY_PROFIT_FLOOR_GUARDIAN,state_restored
2026.06.22 20:51:51,2026.06.22 20:51:45,2026.06.23 00:51:45,A1_DAILY_PROFIT_LOSS_GUARDIAN_V1_ARMED_20260621,1025742,Capital.ComMena-Demo,false,true,true,100.00,true,-100.00,A1_DAILY_PROFIT_LOSS_GUARDIAN_KILL.txt,experimental_demo_kill_switch.txt,A1_DAILY_PROFIT_LOSS_GUARDIAN_STATE.txt,A1_DAILY_PROFIT_LOSS_GUARDIAN_EVENTS.csv,A1_DAILY_PROFIT_LOSS_GUARDIAN_DAILY_SUMMARY.csv,REMOVED_REASON_9,guardian_deinit
2026.06.22 20:52:08,2026.06.22 20:52:02,2026.06.23 00:52:02,A1_DAILY_PROFIT_LOSS_GUARDIAN_V1_ARMED_20260621,1025742,Capital.ComMena-Demo,false,true,true,100.00,true,-100.00,A1_DAILY_PROFIT_LOSS_GUARDIAN_KILL.txt,experimental_demo_kill_switch.txt,A1_DAILY_PROFIT_LOSS_GUARDIAN_STATE.txt,A1_DAILY_PROFIT_LOSS_GUARDIAN_EVENTS.csv,A1_DAILY_PROFIT_LOSS_GUARDIAN_DAILY_SUMMARY.csv,ATTACHED_A1_DAILY_PROFIT_FLOOR_GUARDIAN,state_restored
```
### A2_guardian

Path: `C:\MT5PortableTier1BestEA\MQL5\Files\A2_DAILY_PROFIT_LOSS_GUARDIAN_STARTUP.csv`

```text
2026.06.22 11:20:33,2026.06.22 11:20:28,2026.06.22 15:20:28,A2_DAILY_PROFIT_LOSS_GUARDIAN_V1_ARMED_20260621,1033030,Capital.ComMena-Demo,false,true,true,100.00,true,-100.00,A2_DAILY_PROFIT_LOSS_GUARDIAN_KILL.txt,tier1_bestea_kill_switch.txt,A2_DAILY_PROFIT_LOSS_GUARDIAN_STATE.txt,A2_DAILY_PROFIT_LOSS_GUARDIAN_EVENTS.csv,A2_DAILY_PROFIT_LOSS_GUARDIAN_DAILY_SUMMARY.csv,REMOVED_REASON_9,guardian_deinit
2026.06.22 11:20:40,2026.06.22 11:20:36,2026.06.22 15:20:36,A2_DAILY_PROFIT_LOSS_GUARDIAN_V1_ARMED_20260621,1033030,Capital.ComMena-Demo,false,true,true,100.00,true,-100.00,A2_DAILY_PROFIT_LOSS_GUARDIAN_KILL.txt,tier1_bestea_kill_switch.txt,A2_DAILY_PROFIT_LOSS_GUARDIAN_STATE.txt,A2_DAILY_PROFIT_LOSS_GUARDIAN_EVENTS.csv,A2_DAILY_PROFIT_LOSS_GUARDIAN_DAILY_SUMMARY.csv,ATTACHED_A1_DAILY_PROFIT_FLOOR_GUARDIAN,state_restored
2026.06.22 11:29:35,2026.06.22 11:29:31,2026.06.22 15:29:31,A2_DAILY_PROFIT_LOSS_GUARDIAN_V1_ARMED_20260621,1033030,Capital.ComMena-Demo,false,true,true,100.00,true,-100.00,A2_DAILY_PROFIT_LOSS_GUARDIAN_KILL.txt,tier1_bestea_kill_switch.txt,A2_DAILY_PROFIT_LOSS_GUARDIAN_STATE.txt,A2_DAILY_PROFIT_LOSS_GUARDIAN_EVENTS.csv,A2_DAILY_PROFIT_LOSS_GUARDIAN_DAILY_SUMMARY.csv,REMOVED_REASON_9,guardian_deinit
2026.06.22 11:29:43,2026.06.22 11:29:39,2026.06.22 15:29:39,A2_DAILY_PROFIT_LOSS_GUARDIAN_V1_ARMED_20260621,1033030,Capital.ComMena-Demo,false,true,true,100.00,true,-100.00,A2_DAILY_PROFIT_LOSS_GUARDIAN_KILL.txt,tier1_bestea_kill_switch.txt,A2_DAILY_PROFIT_LOSS_GUARDIAN_STATE.txt,A2_DAILY_PROFIT_LOSS_GUARDIAN_EVENTS.csv,A2_DAILY_PROFIT_LOSS_GUARDIAN_DAILY_SUMMARY.csv,ATTACHED_A1_DAILY_PROFIT_FLOOR_GUARDIAN,state_restored
2026.06.22 20:51:58,2026.06.22 20:51:51,2026.06.23 00:51:51,A2_DAILY_PROFIT_LOSS_GUARDIAN_V1_ARMED_20260621,1033030,Capital.ComMena-Demo,false,true,true,100.00,true,-100.00,A2_DAILY_PROFIT_LOSS_GUARDIAN_KILL.txt,tier1_bestea_kill_switch.txt,A2_DAILY_PROFIT_LOSS_GUARDIAN_STATE.txt,A2_DAILY_PROFIT_LOSS_GUARDIAN_EVENTS.csv,A2_DAILY_PROFIT_LOSS_GUARDIAN_DAILY_SUMMARY.csv,REMOVED_REASON_9,guardian_deinit
2026.06.22 20:52:08,2026.06.22 20:52:02,2026.06.23 00:52:02,A2_DAILY_PROFIT_LOSS_GUARDIAN_V1_ARMED_20260621,1033030,Capital.ComMena-Demo,false,true,true,100.00,true,-100.00,A2_DAILY_PROFIT_LOSS_GUARDIAN_KILL.txt,tier1_bestea_kill_switch.txt,A2_DAILY_PROFIT_LOSS_GUARDIAN_STATE.txt,A2_DAILY_PROFIT_LOSS_GUARDIAN_EVENTS.csv,A2_DAILY_PROFIT_LOSS_GUARDIAN_DAILY_SUMMARY.csv,ATTACHED_A1_DAILY_PROFIT_FLOOR_GUARDIAN,state_restored
```

## Order Log Evidence

No post-maintenance order is required yet because the market/session/signal may not have fired after the relaunch. The first Monday order should add order-log proof with magic `920101`.

### A1_920101

Path: `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files\a1_920101_evening_order_log.csv`

Status: `ORDER_ROW_FOUND`

```text
timestamp_broker,timestamp_utc,timestamp_local,run_id,account_server,account_login,symbol,candidate,candidate_status,family_lifecycle_status,candidate_family_status,experimental_quarantine,canonical_phase2_evidence,phase2_readiness_override,magic,broker_action_allowed,dry_run,cost_suspension_ack_token_present,action,direction,volume,order_mode,spread_at_signal_points,spread_at_order_points,signal_entry_price,request_price,actual_request_price,sl,tp,retcode,retcode_description,order_ticket,deal_ticket,result_price,result_volume,slippage_points,estimated_cost_R,stop_distance_points,account_orders_today,account_open_exposure,reason_code,guard_reason,dirstate_direction,dirstate_regime,dirstate_strength
2026.06.21 22:05:00,2026.06.21 22:04:58,2026.06.22 02:04:58,A1_XAU_920101_EVENING_FORWARD_V0_20260621,Capital.ComMena-Demo,1025742,XAUUSD,breakout_retest,EXPERIMENTAL_QUARANTINE_REVIEW_ONLY,COST_SUSPENDED_CANONICAL,COST_SUSPENDED_CANONICAL,true,false,false,920101,true,false,true,GUARD_BLOCK,LONG,0.00,MARKET_PROXY,95.00,95.00,4155.33,0.00,0.00,0.00,0.00,0,,0,0,0.00,0.00,0.00,0.2008,473.11,0,2,BREAKOUT_RETEST_LONG_DRY_RUN,server_hour_session_gate,0,UNKNOWN,0.000
2026.06.21 22:50:00,2026.06.21 22:49:59,2026.06.22 02:49:59,A1_XAU_920101_EVENING_FORWARD_V0_20260621,Capital.ComMena-Demo,1025742,XAUUSD,breakout_retest,EXPERIMENTAL_QUARANTINE_REVIEW_ONLY,COST_SUSPENDED_CANONICAL,COST_SUSPENDED_CANONICAL,true,false,false,920101,true,false,true,GUARD_BLOCK,LONG,0.00,MARKET_PROXY,50.00,50.00,4154.63,0.00,0.00,0.00,0.00,0,,0,0,0.00,0.00,0.00,0.1044,478.98,0,2,BREAKOUT_RETEST_LONG_DRY_RUN,server_hour_session_gate,0,UNKNOWN,0.000
2026.06.21 22:55:00,2026.06.21 22:54:58,2026.06.22 02:54:58,A1_XAU_920101_EVENING_FORWARD_V0_20260621,Capital.ComMena-Demo,1025742,XAUUSD,breakout_retest,EXPERIMENTAL_QUARANTINE_REVIEW_ONLY,COST_SUSPENDED_CANONICAL,COST_SUSPENDED_CANONICAL,true,false,false,920101,true,false,true,GUARD_BLOCK,LONG,0.00,MARKET_PROXY,50.00,50.00,4154.94,0.00,0.00,0.00,0.00,0,,0,0,0.00,0.00,0.00,0.1520,328.89,0,2,BREAKOUT_RETEST_LONG_DRY_RUN,server_hour_session_gate,0,UNKNOWN,0.000
2026.06.22 00:20:00,2026.06.22 00:19:58,2026.06.22 04:19:58,A1_XAU_920101_EVENING_FORWARD_V0_20260621,Capital.ComMena-Demo,1025742,XAUUSD,breakout_retest,EXPERIMENTAL_QUARANTINE_REVIEW_ONLY,COST_SUSPENDED_CANONICAL,COST_SUSPENDED_CANONICAL,true,false,false,920101,true,false,true,GUARD_BLOCK,LONG,0.00,MARKET_PROXY,50.00,50.00,4162.48,0.00,0.00,0.00,0.00,0,,0,0,0.00,0.00,0.00,0.0315,1589.13,0,2,BREAKOUT_RETEST_LONG_DRY_RUN,server_hour_session_gate,0,UNKNOWN,0.000
2026.06.22 06:50:01,2026.06.22 06:49:57,2026.06.22 10:49:57,A1_XAU_920101_EVENING_FORWARD_V0_20260621,Capital.ComMena-Demo,1025742,XAUUSD,breakout_retest,EXPERIMENTAL_QUARANTINE_REVIEW_ONLY,COST_SUSPENDED_CANONICAL,COST_SUSPENDED_CANONICAL,true,false,false,920101,true,false,true,GUARD_BLOCK,LONG,0.00,MARKET_PROXY,50.00,50.00,4202.37,0.00,0.00,0.00,0.00,0,,0,0,0.00,0.00,0.00,0.0839,596.11,0,2,BREAKOUT_RETEST_LONG_DRY_RUN,server_hour_session_gate,0,UNKNOWN,0.000
2026.06.22 07:10:00,2026.06.22 07:09:56,2026.06.22 11:09:56,A1_XAU_920101_EVENING_FORWARD_V0_20260621,Capital.ComMena-Demo,1025742,XAUUSD,breakout_retest,EXPERIMENTAL_QUARANTINE_REVIEW_ONLY,COST_SUSPENDED_CANONICAL,COST_SUSPENDED_CANONICAL,true,false,false,920101,true,false,true,GUARD_BLOCK,LONG,0.00,MARKET_PROXY,50.00,50.00,4200.92,0.00,0.00,0.00,0.00,0,,0,0,0.00,0.00,0.00,0.1129,442.97,0,2,BREAKOUT_RETEST_LONG_DRY_RUN,server_hour_session_gate,0,UNKNOWN,0.000
2026.06.22 07:20:01,2026.06.22 07:19:57,2026.06.22 11:19:57,A1_XAU_920101_EVENING_FORWARD_V0_20260621,Capital.ComMena-Demo,1025742,XAUUSD,breakout_retest,EXPERIMENTAL_QUARANTINE_REVIEW_ONLY,COST_SUSPENDED_CANONICAL,COST_SUSPENDED_CANONICAL,true,false,false,920101,true,false,true,GUARD_BLOCK,LONG,0.00,MARKET_PROXY,50.00,50.00,4200.81,0.00,0.00,0.00,0.00,0,,0,0,0.00,0.00,0.00,0.1718,291.09,0,2,BREAKOUT_RETEST_LONG_DRY_RUN,server_hour_session_gate,0,UNKNOWN,0.000
```
### A2_920101

Path: `C:\MT5PortableTier1BestEA\MQL5\Files\a2_920101_evening_order_log.csv`

Status: `ORDER_ROW_FOUND`

```text
timestamp_broker,timestamp_utc,timestamp_local,run_id,account_server,account_login,symbol,candidate,candidate_status,family_lifecycle_status,candidate_family_status,experimental_quarantine,canonical_phase2_evidence,phase2_readiness_override,magic,broker_action_allowed,dry_run,cost_suspension_ack_token_present,action,direction,volume,order_mode,spread_at_signal_points,spread_at_order_points,signal_entry_price,request_price,actual_request_price,sl,tp,retcode,retcode_description,order_ticket,deal_ticket,result_price,result_volume,slippage_points,estimated_cost_R,stop_distance_points,account_orders_today,account_open_exposure,reason_code,guard_reason,dirstate_direction,dirstate_regime,dirstate_strength
2026.06.21 22:05:00,2026.06.21 22:04:58,2026.06.22 02:04:58,A2_XAU_920101_EVENING_FORWARD_V0_20260621,Capital.ComMena-Demo,1033030,XAUUSD,breakout_retest,EXPERIMENTAL_QUARANTINE_REVIEW_ONLY,COST_SUSPENDED_CANONICAL,COST_SUSPENDED_CANONICAL,true,false,false,920101,true,false,true,GUARD_BLOCK,LONG,0.00,MARKET_PROXY,95.00,95.00,4155.33,0.00,0.00,0.00,0.00,0,,0,0,0.00,0.00,0.00,0.2008,473.11,0,0,BREAKOUT_RETEST_LONG_DRY_RUN,server_hour_session_gate,0,UNKNOWN,0.000
2026.06.21 22:50:00,2026.06.21 22:49:59,2026.06.22 02:49:59,A2_XAU_920101_EVENING_FORWARD_V0_20260621,Capital.ComMena-Demo,1033030,XAUUSD,breakout_retest,EXPERIMENTAL_QUARANTINE_REVIEW_ONLY,COST_SUSPENDED_CANONICAL,COST_SUSPENDED_CANONICAL,true,false,false,920101,true,false,true,GUARD_BLOCK,LONG,0.00,MARKET_PROXY,50.00,50.00,4154.63,0.00,0.00,0.00,0.00,0,,0,0,0.00,0.00,0.00,0.1044,478.98,0,0,BREAKOUT_RETEST_LONG_DRY_RUN,server_hour_session_gate,0,UNKNOWN,0.000
2026.06.21 22:55:00,2026.06.21 22:54:59,2026.06.22 02:54:59,A2_XAU_920101_EVENING_FORWARD_V0_20260621,Capital.ComMena-Demo,1033030,XAUUSD,breakout_retest,EXPERIMENTAL_QUARANTINE_REVIEW_ONLY,COST_SUSPENDED_CANONICAL,COST_SUSPENDED_CANONICAL,true,false,false,920101,true,false,true,GUARD_BLOCK,LONG,0.00,MARKET_PROXY,50.00,50.00,4154.94,0.00,0.00,0.00,0.00,0,,0,0,0.00,0.00,0.00,0.1520,328.89,0,0,BREAKOUT_RETEST_LONG_DRY_RUN,server_hour_session_gate,0,UNKNOWN,0.000
2026.06.22 00:20:00,2026.06.22 00:19:57,2026.06.22 04:19:57,A2_XAU_920101_EVENING_FORWARD_V0_20260621,Capital.ComMena-Demo,1033030,XAUUSD,breakout_retest,EXPERIMENTAL_QUARANTINE_REVIEW_ONLY,COST_SUSPENDED_CANONICAL,COST_SUSPENDED_CANONICAL,true,false,false,920101,true,false,true,GUARD_BLOCK,LONG,0.00,MARKET_PROXY,50.00,50.00,4162.48,0.00,0.00,0.00,0.00,0,,0,0,0.00,0.00,0.00,0.0315,1589.13,0,0,BREAKOUT_RETEST_LONG_DRY_RUN,server_hour_session_gate,0,UNKNOWN,0.000
2026.06.22 06:50:01,2026.06.22 06:49:57,2026.06.22 10:49:57,A2_XAU_920101_EVENING_FORWARD_V0_20260621,Capital.ComMena-Demo,1033030,XAUUSD,breakout_retest,EXPERIMENTAL_QUARANTINE_REVIEW_ONLY,COST_SUSPENDED_CANONICAL,COST_SUSPENDED_CANONICAL,true,false,false,920101,true,false,true,GUARD_BLOCK,LONG,0.00,MARKET_PROXY,50.00,50.00,4202.37,0.00,0.00,0.00,0.00,0,,0,0,0.00,0.00,0.00,0.0839,596.11,0,0,BREAKOUT_RETEST_LONG_DRY_RUN,server_hour_session_gate,0,UNKNOWN,0.000
2026.06.22 07:10:00,2026.06.22 07:09:56,2026.06.22 11:09:56,A2_XAU_920101_EVENING_FORWARD_V0_20260621,Capital.ComMena-Demo,1033030,XAUUSD,breakout_retest,EXPERIMENTAL_QUARANTINE_REVIEW_ONLY,COST_SUSPENDED_CANONICAL,COST_SUSPENDED_CANONICAL,true,false,false,920101,true,false,true,GUARD_BLOCK,LONG,0.00,MARKET_PROXY,50.00,50.00,4200.92,0.00,0.00,0.00,0.00,0,,0,0,0.00,0.00,0.00,0.1129,442.97,0,0,BREAKOUT_RETEST_LONG_DRY_RUN,server_hour_session_gate,0,UNKNOWN,0.000
2026.06.22 07:20:01,2026.06.22 07:19:57,2026.06.22 11:19:57,A2_XAU_920101_EVENING_FORWARD_V0_20260621,Capital.ComMena-Demo,1033030,XAUUSD,breakout_retest,EXPERIMENTAL_QUARANTINE_REVIEW_ONLY,COST_SUSPENDED_CANONICAL,COST_SUSPENDED_CANONICAL,true,false,false,920101,true,false,true,GUARD_BLOCK,LONG,0.00,MARKET_PROXY,50.00,50.00,4200.81,0.00,0.00,0.00,0.00,0,,0,0,0.00,0.00,0.00,0.1718,291.09,0,0,BREAKOUT_RETEST_LONG_DRY_RUN,server_hour_session_gate,0,UNKNOWN,0.000
```

## Claude Review Focus

- Confirm the refreshed inventory supersedes the stale pre-fix RUNTIME_CHART_INVENTORY_FORENSIC_2026_06_21.csv.
- Confirm A1 chart03 is the restored XAU breakout_retest executor with broker action enabled.
- Confirm A1 chart01/chart02/chart18/chart19/chart20 and chart21 are disarmed.
- Confirm A2 chart02 is the aligned XAU breakout_retest executor with broker action enabled.
- Confirm A1/A2 guardians are active with +100 AED daily floor and -100 AED daily loss stop.
- Confirm 920101 is derived from source formula plus startup mutex proof, while order-log proof is pending until the first post-maintenance order.
