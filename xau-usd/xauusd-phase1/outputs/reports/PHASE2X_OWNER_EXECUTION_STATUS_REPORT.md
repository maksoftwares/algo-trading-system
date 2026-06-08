# Phase 2X Owner Execution Status Report

Overall status: PASS

Phase 2X owner-execution status. Experimental demo only; no canonical Phase 2, no live trading, and no real capital authorization.

Created at UTC: `2026-06-08T12:00:07.987010Z`

## Boundary

- Phase 2X can approve only quarantined experimental demo execution.
- Phase 2X cannot approve canonical Phase 2.
- Phase 2X cannot approve live trading or real capital.
- Phase 2X cannot unsuspend the cost-suspended breakout-retest family.
- Phase 2X cannot create same-family diversification claims.

- Phase 2X demo execution attached: `True`
- Owner exec root: `C:\MT5PortableP2WeaknessOwnerExec`
- Sent orders observed: `0`
- Order summary: `{'rows': 0, 'actions': {}, 'order_send_ok': 0, 'guard_blocks': 0, 'estimated_cost_r_min': None, 'estimated_cost_r_mean': None, 'estimated_cost_r_max': None}`

## Logs

- Startup log: `C:\MT5PortableP2WeaknessOwnerExec\MQL5\Files\p2weakness_br_v1_startup_xauusd.csv`
- Signal log: `C:\MT5PortableP2WeaknessOwnerExec\MQL5\Files\p2weakness_br_v1_signal_log_xauusd.csv`
- Order log: `C:\MT5PortableP2WeaknessOwnerExec\MQL5\Files\p2weakness_br_v1_order_log_xauusd.csv`

## Latest Startup

- `{'timestamp_broker': '2026.06.08 11:53:45', 'timestamp_utc': '2026.06.08 11:53:40', 'timestamp_local': '2026.06.08 15:53:40', 'run_id': 'P2WEAKNESS_BR_V1', 'account_server': 'Capital.ComMena-Demo', 'account_login': '****742', 'symbol': 'XAUUSD', 'candidate': 'breakout_retest', 'candidate_status': 'EXPERIMENTAL_QUARANTINE_REVIEW_ONLY', 'family_lifecycle_status': 'COST_SUSPENDED_CANONICAL', 'magic': '931000', 'order_comment': 'P2WEAKNESS_BR_V1', 'dry_run': 'false', 'broker_action_allowed': 'true', 'allowed_account_logins': '****742', 'authorization_token_present': 'true', 'source_default_safe': 'true', 'owner_authorized_set_used': 'true', 'experimental_authorization_token_present': 'true', 'cost_suspension_acknowledged': 'true', 'max_orders_per_day': '2', 'max_account_orders_per_day': '3', 'max_family_open_positions': '1', 'duplicate_lock_bars': '12', 'max_estimated_cost_R': '0.1500', 'max_measured_spread_points': '75.00', 'kill_switch_file': 'p2weakness_br_v1_kill_switch.txt', 'startup_status': 'ATTACHED_OWNER_AUTHORIZED_WEAKNESS_REVIEW_DEMO_EXECUTOR_ENABLED'}`

## Latest Signal

- `{'timestamp_broker': '2026.06.08 12:00:00', 'timestamp_utc': '2026.06.08 11:59:55', 'timestamp_local': '2026.06.08 15:59:55', 'run_id': 'P2WEAKNESS_BR_V1', 'account_server': 'Capital.ComMena-Demo', 'account_login': '****742', 'symbol': 'XAUUSD', 'candidate': 'breakout_retest', 'candidate_status': 'EXPERIMENTAL_QUARANTINE_REVIEW_ONLY', 'family_lifecycle_status': 'COST_SUSPENDED_CANONICAL', 'magic': '931000', 'order_comment': 'P2WEAKNESS_BR_V1', 'm5_bar_time': '2026.06.08 12:00:00', 'bid': '4330.84', 'ask': '4331.34', 'spread_points': '50.00', 'stage': 'WAIT_LEVEL_BREAK_RETEST', 'direction': 'LONG', 'would_signal': 'false', 'reason_code': 'no_long_breakout_retest_candidate', 'level_kind': 'none', 'level_price': '0.00', 'entry_price': '0.00', 'stop_loss': '0.00', 'take_profit': '0.00', 'stop_distance_points': '0.00', 'duplicate_lock_key': ''}`

## Checks

| Check | Status | Evidence |
|---|---|---|
| owner_exec_terminal_root_present | PASS | C:\MT5PortableP2WeaknessOwnerExec |
| startup_log_present | PASS | C:\MT5PortableP2WeaknessOwnerExec\MQL5\Files\p2weakness_br_v1_startup_xauusd.csv |
| attached_owner_authorized | PASS | startup_status='ATTACHED_OWNER_AUTHORIZED_WEAKNESS_REVIEW_DEMO_EXECUTOR_ENABLED' |
| broker_action_enabled_for_demo | PASS | dry_run='false'; broker_action_allowed='true' |
| demo_server_only | PASS | account_server='Capital.ComMena-Demo' |
| account_login_present_masked | PASS | ****742 |
| magic_931000 | PASS | magic='931000' |
| symbol_xauusd | PASS | symbol='XAUUSD' |
| fixed_lot_guard | PASS | max_estimated_cost_R='0.1500' |
| family_exposure_guard | PASS | max_family_open_positions='1' |
| signal_log_active | PASS | signal_rows=3 |
| all_order_rows_magic_931000 | PASS | order_rows=0 |
| all_order_rows_symbol_xauusd | PASS | order_rows=0 |
| sent_lots_lte_0_01 | PASS | sent_orders=0 |
| sent_cost_r_lte_0_15 | PASS | sent_orders=0 |
