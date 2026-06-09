# Phase 2 Repaired Demo Executor Attachments

Status: REPAIRED_EXECUTORS_APPENDED_TO_DEMO_TERMINAL

Owner-requested experimental demo repair lane. Existing demo executor charts are preserved; only prior repair-lane charts are replaced to avoid duplicates.

Demo only; no live trading; does not authorize canonical Phase 2 or real capital.

Run ID: `phase2-demo-repair-executor-v1`
Attachment count: `3`
Terminal: `C:\Program Files\MetaTrader 5\terminal64.exe`
Data folder: `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075`
Profile backup: `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\_codex_quarantine\profile_backups\default_profile_before_repair_append_20260609_085316`
Existing profile preserved: `True`
Removed prior repair charts: `['chart18.chr', 'chart19.chr', 'chart20.chr']`
Magic namespace: `921000-921999`
Comment prefix: `P2REPAIR`
Account order cap: `UNLIMITED`
Repair time bucket clock: `UTC+240 minutes (Dubai)`
Kill switch: `phase2_demo_repair_kill_switch.txt` / `ABSENT`

| Candidate | Symbol | Lot | Magic | Filter | Qualification | Logs |
|---|---|---:|---:|---|---|---|
| symbol_normalized_round_retest_v0_repair_v1 | XAUUSD | 0.01 | 921101 | XAUUSD Evening 16:00-19:59 SHORT only | PHASE2_REPAIR_CANDIDATE_RULES.csv:PREFERRED_CLUSTER | phase2_demo_repair_executor_order_log_v1_symbol_normalized_round_retest_v0_repair_v1_xauusd.csv |
| session_extreme_retest_v0_repair_v1 | XAUUSD | 0.01 | 921201 | XAUUSD Afternoon 12:00-15:59 or Evening 16:00-19:59 SHORT only | PHASE2_REPAIR_CANDIDATE_RULES.csv:PREFERRED_CLUSTER | phase2_demo_repair_executor_order_log_v1_session_extreme_retest_v0_repair_v1_xauusd.csv |
| session_extreme_retest_v0_repair_v1 | EURUSD | 0.05 | 921202 | EURUSD Night 20:00-05:59 SHORT only | PHASE2_REPAIR_CANDIDATE_RULES.csv:PREFERRED_CLUSTER | phase2_demo_repair_executor_order_log_v1_session_extreme_retest_v0_repair_v1_eurusd.csv |

These repaired charts are additive. They do not delete the existing experimental demo executor charts.
Round-number repair v1 is not attached for broker action because the research output marks it rebuild/observer-only.
