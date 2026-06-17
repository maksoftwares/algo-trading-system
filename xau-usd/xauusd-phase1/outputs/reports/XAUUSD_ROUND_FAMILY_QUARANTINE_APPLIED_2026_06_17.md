# XAUUSD Round-Family Quarantine Applied - 2026-06-17

Overall status: `ROUND_FAMILY_QUARANTINE_APPLIED`

Demo-only controlled maintenance window. No live/real-capital authorization and no canonical Phase 2 approval.

## Owner Decision

- Owner: `Muhammad Ali Khan`
- Decision: `APPROVE_BOTH_ITEMS`
- Approved candidates: `round_number_retest_v0, symbol_normalized_round_retest_v0`
- Owner packet: `xau-usd/xauusd-phase1/docs/XAUUSD_ROUND_FAMILY_QUARANTINE_OWNER_DECISION_2026_06_17.md`
- Reviewer sign-off: `XAUUSD_REVIEWER_SIGNOFF_ROUND_QUARANTINE_2026_06_17.md`

## Scope

- Symbol: `XAUUSD`
- Targets: `round_number_retest_v0, symbol_normalized_round_retest_v0`
- Out of scope: `broad afternoon ban, direction-only rule, cost-threshold runtime rule, breakout_retest changes, swing_breakout_retest_v0 changes, EURUSD/GBPUSD round-family changes, repair-v1 lane changes, live trading, real capital`

## Maintenance Window

- Terminal: `C:\Program Files\MetaTrader 5\terminal64.exe`
- Data folder: `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075`
- Profile: `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Profiles\Charts\Default`
- Terminal closed before edit: `true`
- Terminal relaunched: `true`
- Profile backup: `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\_codex_quarantine\profile_backups\default_profile_before_round_family_quarantine_20260617_112219`

## Target Charts

| chart | symbol | candidate | dry_run | broker_action_allowed | candidate_status | signal_log | order_log |
| --- | --- | --- | --- | --- | --- | --- | --- |
| chart09.chr | XAUUSD | symbol_normalized_round_retest_v0 | true | false | OWNER_APPROVED_ROUND_FAMILY_QUARANTINED | experimental_demo_executor_signal_log_v02_symbol_normalized_round_retest_v0_xauusd.csv | experimental_demo_executor_order_log_v02_symbol_normalized_round_retest_v0_xauusd.csv |
| chart11.chr | XAUUSD | round_number_retest_v0 | true | false | OWNER_APPROVED_ROUND_FAMILY_QUARANTINED | experimental_demo_executor_signal_log_v02_round_number_retest_v0_xauusd.csv | experimental_demo_executor_order_log_v02_round_number_retest_v0_xauusd.csv |

## Protected Breakout Charts

| chart | symbol | candidate | dry_run | broker_action_allowed | candidate_status | signal_log | order_log |
| --- | --- | --- | --- | --- | --- | --- | --- |
| chart03.chr | XAUUSD | breakout_retest | false | true | EXPERIMENTAL_QUARANTINE_REVIEW_ONLY | experimental_demo_executor_signal_log_v02_breakout_retest_xauusd.csv | experimental_demo_executor_order_log_v02_breakout_retest_xauusd.csv |
| chart06.chr | XAUUSD | swing_breakout_retest_v0 | false | true | EXPERIMENTAL_QUARANTINE_REVIEW_ONLY | experimental_demo_executor_signal_log_v02_swing_breakout_retest_v0_xauusd.csv | experimental_demo_executor_order_log_v02_swing_breakout_retest_v0_xauusd.csv |

## Verification

| check | status | detail |
| --- | --- | --- |
| round_number_retest_v0_quarantined | PASS | {"broker_action_allowed": "false", "candidate": "round_number_retest_v0", "candidate_status": "OWNER_APPROVED_ROUND_FAMILY_QUARANTINED", "chart": "chart11.chr", "dry_run": "true", "expert": "Phase2ExperimentalDemoExecutor", "order_log": "experimental_demo_executor_order_log_v02_round_number_retest_v0_xauusd.csv", "path": "C:\\Users\\ZHAO ZHU INFORMATION\\AppData\\Roaming\\MetaQuotes\\Terminal\\D0E8209F77C8CF37AD8BF550E51FF075\\MQL5\\Profiles\\Charts\\Default\\chart11.chr", "qualified_symbols": "GBPUSD,XAUUSD", "signal_log": "experimental_demo_executor_signal_log_v02_round_number_retest_v0_xauusd.csv", "startup_log": "experimental_demo_executor_startup_v02_round_number_retest_v0_xauusd.csv", "symbol": "XAUUSD", "target_symbol": "XAUUSD"} |
| symbol_normalized_round_retest_v0_quarantined | PASS | {"broker_action_allowed": "false", "candidate": "symbol_normalized_round_retest_v0", "candidate_status": "OWNER_APPROVED_ROUND_FAMILY_QUARANTINED", "chart": "chart09.chr", "dry_run": "true", "expert": "Phase2ExperimentalDemoExecutor", "order_log": "experimental_demo_executor_order_log_v02_symbol_normalized_round_retest_v0_xauusd.csv", "path": "C:\\Users\\ZHAO ZHU INFORMATION\\AppData\\Roaming\\MetaQuotes\\Terminal\\D0E8209F77C8CF37AD8BF550E51FF075\\MQL5\\Profiles\\Charts\\Default\\chart09.chr", "qualified_symbols": "EURUSD,GBPUSD,XAUUSD", "signal_log": "experimental_demo_executor_signal_log_v02_symbol_normalized_round_retest_v0_xauusd.csv", "startup_log": "experimental_demo_executor_startup_v02_symbol_normalized_round_retest_v0_xauusd.csv", "symbol": "XAUUSD", "target_symbol": "XAUUSD"} |
| protected_breakout_core_unchanged | PASS | before=[{'chart': 'chart03.chr', 'symbol': 'XAUUSD', 'expert': 'Phase2ExperimentalDemoExecutor', 'dry_run': 'false', 'broker_action_allowed': 'true', 'candidate': 'breakout_retest', 'candidate_status': 'EXPERIMENTAL_QUARANTINE_REVIEW_ONLY', 'target_symbol': 'XAUUSD', 'qualified_symbols': 'EURUSD,GBPUSD,XAUUSD'}, {'chart': 'chart06.chr', 'symbol': 'XAUUSD', 'expert': 'Phase2ExperimentalDemoExecutor', 'dry_run': 'false', 'broker_action_allowed': 'true', 'candidate': 'swing_breakout_retest_v0', 'candidate_status': 'EXPERIMENTAL_QUARANTINE_REVIEW_ONLY', 'target_symbol': 'XAUUSD', 'qualified_symbols': 'EURUSD,GBPUSD,XAUUSD'}]; after=[{'chart': 'chart03.chr', 'symbol': 'XAUUSD', 'expert': 'Phase2ExperimentalDemoExecutor', 'dry_run': 'false', 'broker_action_allowed': 'true', 'candidate': 'breakout_retest', 'candidate_status': 'EXPERIMENTAL_QUARANTINE_REVIEW_ONLY', 'target_symbol': 'XAUUSD', 'qualified_symbols': 'EURUSD,GBPUSD,XAUUSD'}, {'chart': 'chart06.chr', 'symbol': 'XAUUSD', 'expert': 'Phase2ExperimentalDemoExecutor', 'dry_run': 'false', 'broker_action_allowed': 'true', 'candidate': 'swing_breakout_retest_v0', 'candidate_status': 'EXPERIMENTAL_QUARANTINE_REVIEW_ONLY', 'target_symbol': 'XAUUSD', 'qualified_symbols': 'EURUSD,GBPUSD,XAUUSD'}] |
| only_target_charts_changed_by_script | PASS | changed=['chart09.chr', 'chart11.chr'] expected=['chart09.chr', 'chart11.chr'] |
| target_order_logs_no_new_rows_during_window | PASS | before={'experimental_demo_executor_order_log_v02_symbol_normalized_round_retest_v0_xauusd.csv': 518, 'experimental_demo_executor_order_log_v02_round_number_retest_v0_xauusd.csv': 518}; after={'experimental_demo_executor_order_log_v02_symbol_normalized_round_retest_v0_xauusd.csv': 518, 'experimental_demo_executor_order_log_v02_round_number_retest_v0_xauusd.csv': 518} |

## Order Log Row Counts

| order_log | before_rows | after_rows |
| --- | --- | --- |
| experimental_demo_executor_order_log_v02_round_number_retest_v0_xauusd.csv | 518 | 518 |
| experimental_demo_executor_order_log_v02_symbol_normalized_round_retest_v0_xauusd.csv | 518 | 518 |

## Startup Log Row Counts After Relaunch

| startup_log | rows |
| --- | --- |
| experimental_demo_executor_startup_v02_symbol_normalized_round_retest_v0_xauusd.csv | 36 |
| experimental_demo_executor_startup_v02_round_number_retest_v0_xauusd.csv | 36 |

Note: `Phase2ExperimentalDemoExecutor` intentionally refuses to initialize when `InpDryRunOnly=true` or `InpBrokerActionAllowed=false`. For this reversible quarantine, the profile input values are the broker-action proof; existing historical logs are preserved.

## Rollback

- Backup: `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\_codex_quarantine\profile_backups\default_profile_before_round_family_quarantine_20260617_112219`
- Instruction: Close the standard MT5 terminal, replace the Default profile with this backup, then relaunch.
