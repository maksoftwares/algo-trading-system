# A1 BTC Breakout Executor Attachment - 2026-06-18

Status: `A1_BTC_BREAKOUT_EXECUTOR_APPENDED`

Owner-requested A1 demo-only BTCUSD breakout experiment. This is not a canonical Phase 2 approval, not live trading, and not real capital.

## Attachment

- Account: `1025742 / Capital.ComMena-Demo`
- Symbol: `BTCUSD`
- Candidate: `breakout_retest`
- Magic: `920105`
- Lot: `0.01`
- Chart: `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Profiles\Charts\Default\chart25.chr`
- Profile backup: `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\_codex_quarantine\profile_backups\default_profile_before_a1_btc_breakout_append_20260617_222111`
- Compile log: `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Logs\compile_Phase2ExperimentalDemoExecutor_a1_btc.log`

## Boundary

- Demo only.
- Not canonical Phase 2.
- Not live trading.
- BTC has no approved Phase 0 edge; this is an owner-requested experiment.
- Existing charts were preserved; this script appended one BTCUSD chart only.

## Symbol Check

- Broker symbol status: `SYMBOL_AVAILABLE`
- Visible after select: `True`
- Tick present: `True`
- Volume min/step: `0.01` / `0.01`

## Startup Tail

- `timestamp_broker,timestamp_utc,timestamp_local,run_id,account_server,symbol,candidate,candidate_status,family_lifecycle_status,qualified_symbols,account_login,allowed_account_logins,authorized_candidates,dry_run,broker_action_allowed,observer_supported,authorization_token_present,cost_suspension_ack_token_present,account_max_orders_per_day,account_max_open_positions,max_estimated_cost_R,max_measured_spread_points,kill_switch_file,startup_status`
- `2026.06.17 22:21:16,2026.06.17 22:21:14,2026.06.18 02:21:14,phase2-a1-btc-breakout-experiment-v0.1,Capital.ComMena-Demo,BTCUSD,breakout_retest,BTC_EXPERIMENTAL_DEMO_REVIEW_ONLY,COST_SUSPENDED_CANONICAL,BTCUSD,1025742,1025742,breakout_retest,false,true,true,true,true,0,UNLIMITED,0.0000,0.00,experimental_demo_kill_switch.txt,GV_MUTEX_NAMESPACE_SELF_TEST_PASS name=FAMMUX_SELFTEST_1025742_20260617_222114`
- `2026.06.17 22:21:16,2026.06.17 22:21:14,2026.06.18 02:21:14,phase2-a1-btc-breakout-experiment-v0.1,Capital.ComMena-Demo,BTCUSD,breakout_retest,BTC_EXPERIMENTAL_DEMO_REVIEW_ONLY,COST_SUSPENDED_CANONICAL,BTCUSD,1025742,1025742,breakout_retest,false,true,true,true,true,0,UNLIMITED,0.0000,0.00,experimental_demo_kill_switch.txt,ATTACHED_DEMO_EXECUTOR_ENABLED`
