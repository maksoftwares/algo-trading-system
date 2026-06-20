# A1/A2 920101 Maintenance Supplemental Verification - 2026-06-21

Status: `PASS_WITH_ORDER_LOG_PENDING`

Created UTC: `2026-06-20T22:25:27+00:00`

This is a read-only verification report. It refreshes the stale runtime chart inventory and surfaces startup identity proof after the A1/A2 920101 maintenance. It does not change MT5 runtime state.

## Checks

| Check | Status | Detail |
|---|---|---|
| a1_chart03_920101_active | `PASS` | A1 chart03.chr XAUUSD Phase2ExperimentalDemoExecutor BROKER_ACTION_ENABLED magic=920101 |
| a2_chart02_920101_active | `PASS` | A2 chart02.chr XAUUSD Phase2ExperimentalDemoExecutor BROKER_ACTION_ENABLED magic=920101 |
| a1_non_spec_lanes_disarmed | `PASS` | A1 chart01.chr EURUSD Phase2ExperimentalDemoExecutor DISARMED_DRY_RUN magic=920102; A1 chart02.chr GBPUSD Phase2ExperimentalDemoExecutor DISARMED_DRY_RUN magic=920104; A1 chart18.chr XAUUSD Phase2ExperimentalDemoRepairExecutor DISARMED_DRY_RUN magic=; A1 chart19.chr XAUUSD Phase2ExperimentalDemoRepairExecutor DISARMED_DRY_RUN magic=; A1 chart20.chr EURUSD Phase2ExperimentalDemoRepairExecutor DISARMED_DRY_RUN magic= |
| a1_wr50_disarmed | `PASS` | A1 chart21.chr XAUUSD WR50_BreakoutWideStop_v0 DISARMED_DEMO_TRADING_FALSE magic=930300 |
| a1_guardian_active | `PASS` | A1 chart26.chr XAUUSD Account1DailyProfitFloorGuardian GUARDIAN_CLOSE_ACTION_ENABLED magic= |
| a2_guardian_active | `PASS` | A2 chart03.chr XAUUSD Account1DailyProfitFloorGuardian GUARDIAN_CLOSE_ACTION_ENABLED magic= |
| a3_no_broker_action_enabled | `PASS` | A3 has no broker-action enabled rows in inspected profile. |
| a1_startup_mentions_920101 | `PASS` | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files\a1_920101_evening_startup_log.csv |
| a2_startup_mentions_920101 | `PASS` | C:\MT5PortableTier1BestEA\MQL5\Files\a2_920101_evening_startup_log.csv |
| a1_guardian_startup_active | `PASS` | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files\A1_DAILY_PROFIT_LOSS_GUARDIAN_STARTUP.csv |
| a2_guardian_startup_active | `PASS` | C:\MT5PortableTier1BestEA\MQL5\Files\A2_DAILY_PROFIT_LOSS_GUARDIAN_STARTUP.csv |
| a1_first_order_log_proof | `PENDING` | No post-maintenance A1 920101 order row yet; expected until market/session signal fires. |
| a2_first_order_log_proof | `PENDING` | No post-maintenance A2 920101 order row yet; expected until market/session signal fires. |

## Key Runtime Inventory

Full refreshed inventory CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\RUNTIME_CHART_INVENTORY_FORENSIC_2026_06_21.csv`

| Lane | Chart | Symbol | Expert | State | Derived magic | Dry-run | Broker action | Demo trading | Session | Account |
|---|---|---|---|---|---:|---|---|---|---|---|
| A1 | chart01.chr | EURUSD | `Phase2ExperimentalDemoExecutor` | `DISARMED_DRY_RUN` | `920102` | `true` | `false` | `` | `12->1` | `1025742` |
| A1 | chart02.chr | GBPUSD | `Phase2ExperimentalDemoExecutor` | `DISARMED_DRY_RUN` | `920104` | `true` | `false` | `` | `12->1` | `1025742` |
| A1 | chart03.chr | XAUUSD | `Phase2ExperimentalDemoExecutor` | `BROKER_ACTION_ENABLED` | `920101` | `false` | `true` | `` | `12->15` | `1025742` |
| A1 | chart18.chr | XAUUSD | `Phase2ExperimentalDemoRepairExecutor` | `DISARMED_DRY_RUN` | `` | `true` | `false` | `` | `12->1` | `1025742` |
| A1 | chart19.chr | XAUUSD | `Phase2ExperimentalDemoRepairExecutor` | `DISARMED_DRY_RUN` | `` | `true` | `false` | `` | `12->1` | `1025742` |
| A1 | chart20.chr | EURUSD | `Phase2ExperimentalDemoRepairExecutor` | `DISARMED_DRY_RUN` | `` | `true` | `false` | `` | `12->1` | `1025742` |
| A1 | chart21.chr | XAUUSD | `WR50_BreakoutWideStop_v0` | `DISARMED_DEMO_TRADING_FALSE` | `930300` | `` | `` | `false` | `12->1` | `` |
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
timestamp_broker,timestamp_utc,timestamp_local,run_id,account_server,symbol,candidate,candidate_status,family_lifecycle_status,qualified_symbols,account_login,allowed_account_logins,authorized_candidates,dry_run,broker_action_allowed,observer_supported,authorization_token_present,cost_suspension_ack_token_present,account_max_orders_per_day,account_max_open_positions,max_estimated_cost_R,max_measured_spread_points,kill_switch_file,startup_status
2026.06.20 22:07:25,2026.06.20 22:07:19,2026.06.21 02:07:19,A1_XAU_920101_EVENING_FORWARD_V0_20260621,Capital.ComMena-Demo,XAUUSD,breakout_retest,EXPERIMENTAL_QUARANTINE_REVIEW_ONLY,COST_SUSPENDED_CANONICAL,XAUUSD,1025742,1025742,breakout_retest,false,true,true,true,true,0,UNLIMITED,0.3000,75.00,experimental_demo_kill_switch.txt,GV_MUTEX_NAMESPACE_SELF_TEST_PASS name=FAMMUX_SELFTEST_1025742_XAUUSD_920101_20260620_220719
2026.06.20 22:07:25,2026.06.20 22:07:19,2026.06.21 02:07:19,A1_XAU_920101_EVENING_FORWARD_V0_20260621,Capital.ComMena-Demo,XAUUSD,breakout_retest,EXPERIMENTAL_QUARANTINE_REVIEW_ONLY,COST_SUSPENDED_CANONICAL,XAUUSD,1025742,1025742,breakout_retest,false,true,true,true,true,0,UNLIMITED,0.3000,75.00,experimental_demo_kill_switch.txt,ATTACHED_DEMO_EXECUTOR_ENABLED
```
### A2_920101

Path: `C:\MT5PortableTier1BestEA\MQL5\Files\a2_920101_evening_startup_log.csv`

```text
timestamp_broker,timestamp_utc,timestamp_local,run_id,account_server,symbol,candidate,candidate_status,family_lifecycle_status,qualified_symbols,account_login,allowed_account_logins,authorized_candidates,dry_run,broker_action_allowed,observer_supported,authorization_token_present,cost_suspension_ack_token_present,account_max_orders_per_day,account_max_open_positions,max_estimated_cost_R,max_measured_spread_points,kill_switch_file,startup_status
2026.06.19 20:58:59,2026.06.20 22:07:21,2026.06.21 02:07:21,A2_XAU_920101_EVENING_FORWARD_V0_20260621,Capital.ComMena-Demo,XAUUSD,breakout_retest,EXPERIMENTAL_QUARANTINE_REVIEW_ONLY,COST_SUSPENDED_CANONICAL,XAUUSD,1033030,1033030,breakout_retest,false,true,true,true,true,0,UNLIMITED,0.3000,75.00,tier1_bestea_kill_switch.txt,GV_MUTEX_NAMESPACE_SELF_TEST_PASS name=FAMMUX_SELFTEST_1033030_XAUUSD_920101_20260620_220721
2026.06.19 20:58:59,2026.06.20 22:07:21,2026.06.21 02:07:21,A2_XAU_920101_EVENING_FORWARD_V0_20260621,Capital.ComMena-Demo,XAUUSD,breakout_retest,EXPERIMENTAL_QUARANTINE_REVIEW_ONLY,COST_SUSPENDED_CANONICAL,XAUUSD,1033030,1033030,breakout_retest,false,true,true,true,true,0,UNLIMITED,0.3000,75.00,tier1_bestea_kill_switch.txt,ATTACHED_DEMO_EXECUTOR_ENABLED
```
### A1_guardian

Path: `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files\A1_DAILY_PROFIT_LOSS_GUARDIAN_STARTUP.csv`

```text
timestamp_broker,timestamp_utc,timestamp_dubai,run_id,account_login,server,dry_run,close_action_allowed,owner_token_present,daily_floor_aed,daily_loss_stop_enabled,daily_loss_stop_aed,guardian_kill_switch_file,entry_halt_file,state_file,event_log,daily_summary_log,startup_status,detail
2026.06.20 22:07:25,2026.06.20 22:07:19,2026.06.21 02:07:19,A1_DAILY_PROFIT_LOSS_GUARDIAN_V1_ARMED_20260621,1025742,Capital.ComMena-Demo,false,true,true,100.00,true,-100.00,A1_DAILY_PROFIT_LOSS_GUARDIAN_KILL.txt,experimental_demo_kill_switch.txt,A1_DAILY_PROFIT_LOSS_GUARDIAN_STATE.txt,A1_DAILY_PROFIT_LOSS_GUARDIAN_EVENTS.csv,A1_DAILY_PROFIT_LOSS_GUARDIAN_DAILY_SUMMARY.csv,ATTACHED_A1_DAILY_PROFIT_FLOOR_GUARDIAN,state_initialized
```
### A2_guardian

Path: `C:\MT5PortableTier1BestEA\MQL5\Files\A2_DAILY_PROFIT_LOSS_GUARDIAN_STARTUP.csv`

```text
timestamp_broker,timestamp_utc,timestamp_dubai,run_id,account_login,server,dry_run,close_action_allowed,owner_token_present,daily_floor_aed,daily_loss_stop_enabled,daily_loss_stop_aed,guardian_kill_switch_file,entry_halt_file,state_file,event_log,daily_summary_log,startup_status,detail
2026.06.19 20:58:59,2026.06.20 22:07:21,2026.06.21 02:07:21,A2_DAILY_PROFIT_LOSS_GUARDIAN_V1_ARMED_20260621,1033030,Capital.ComMena-Demo,false,true,true,100.00,true,-100.00,A2_DAILY_PROFIT_LOSS_GUARDIAN_KILL.txt,tier1_bestea_kill_switch.txt,A2_DAILY_PROFIT_LOSS_GUARDIAN_STATE.txt,A2_DAILY_PROFIT_LOSS_GUARDIAN_EVENTS.csv,A2_DAILY_PROFIT_LOSS_GUARDIAN_DAILY_SUMMARY.csv,ATTACHED_A1_DAILY_PROFIT_FLOOR_GUARDIAN,state_initialized
```

## Order Log Evidence

No post-maintenance order is required yet because the market/session/signal may not have fired after the relaunch. The first Monday order should add order-log proof with magic `920101`.

### A1_920101

Path: `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files\a1_920101_evening_order_log.csv`

Status: `PENDING_FIRST_ORDER`

```text
timestamp_broker,timestamp_utc,timestamp_local,run_id,account_server,account_login,symbol,candidate,candidate_status,family_lifecycle_status,candidate_family_status,experimental_quarantine,canonical_phase2_evidence,phase2_readiness_override,magic,broker_action_allowed,dry_run,cost_suspension_ack_token_present,action,direction,volume,order_mode,spread_at_signal_points,spread_at_order_points,signal_entry_price,request_price,actual_request_price,sl,tp,retcode,retcode_description,order_ticket,deal_ticket,result_price,result_volume,slippage_points,estimated_cost_R,stop_distance_points,account_orders_today,account_open_exposure,reason_code,guard_reason,dirstate_direction,dirstate_regime,dirstate_strength
```
### A2_920101

Path: `C:\MT5PortableTier1BestEA\MQL5\Files\a2_920101_evening_order_log.csv`

Status: `PENDING_FIRST_ORDER`

```text
timestamp_broker,timestamp_utc,timestamp_local,run_id,account_server,account_login,symbol,candidate,candidate_status,family_lifecycle_status,candidate_family_status,experimental_quarantine,canonical_phase2_evidence,phase2_readiness_override,magic,broker_action_allowed,dry_run,cost_suspension_ack_token_present,action,direction,volume,order_mode,spread_at_signal_points,spread_at_order_points,signal_entry_price,request_price,actual_request_price,sl,tp,retcode,retcode_description,order_ticket,deal_ticket,result_price,result_volume,slippage_points,estimated_cost_R,stop_distance_points,account_orders_today,account_open_exposure,reason_code,guard_reason,dirstate_direction,dirstate_regime,dirstate_strength
```

## Claude Review Focus

- Confirm the refreshed inventory supersedes the stale pre-fix RUNTIME_CHART_INVENTORY_FORENSIC_2026_06_21.csv.
- Confirm A1 chart03 is the restored XAU breakout_retest executor with broker action enabled.
- Confirm A1 chart01/chart02/chart18/chart19/chart20 and chart21 are disarmed.
- Confirm A2 chart02 is the aligned XAU breakout_retest executor with broker action enabled.
- Confirm A1/A2 guardians are active with +100 AED daily floor and -100 AED daily loss stop.
- Confirm 920101 is derived from source formula plus startup mutex proof, while order-log proof is pending until the first post-maintenance order.
