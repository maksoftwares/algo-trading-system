# Phase 2 Experimental Demo Executor Attachments

Status: EXECUTORS_ATTACHED_TO_DEMO_TERMINAL

Experimental demo executor setup only. Attachments may place small orders only on a demo server after broker_action_allowed=true; this does not authorize live trading.

Run ID: `phase2-experimental-demo-executor-v0.2`
Attachment count: 14
Terminal: `C:\Program Files\MetaTrader 5\terminal64.exe`
Data folder: `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075`
Profile backup: `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\_codex_quarantine\profile_backups\default_profile_before_demo_attach_20260608_124303`
Executor log backup: `none`
Authorized candidates: `breakout_retest,swing_breakout_retest_v0,symbol_normalized_round_retest_v0,round_number_retest_v0,session_extreme_retest_v0`
Default candidate status: `EXPERIMENTAL_QUARANTINE_REVIEW_ONLY`
Family lifecycle status: `COST_SUSPENDED_CANONICAL`
Cost-suspension acknowledgement configured: `True`
Account order cap: `24`
Account exposure cap: `3`
Max estimated cost R: `0.3`
Max measured spread points: `75.0`

| Candidate | Research status | Executor status | Family lifecycle | Symbol | Lot | Executor | Qualification |
|---|---|---|---|---:|---:|---|---|
| breakout_retest | ACCEPTED | EXPERIMENTAL_QUARANTINE_REVIEW_ONLY | COST_SUSPENDED_CANONICAL | EURUSD | 0.05 | demo_order_executor | breakout_retest_multisymbol_summary.csv:PASS |
| breakout_retest | ACCEPTED | EXPERIMENTAL_QUARANTINE_REVIEW_ONLY | COST_SUSPENDED_CANONICAL | GBPUSD | 0.01 | demo_order_executor | experimental_replacement_for_USDJPY:breakout_retest_multisymbol_summary.csv:PASS |
| breakout_retest | ACCEPTED | EXPERIMENTAL_QUARANTINE_REVIEW_ONLY | COST_SUSPENDED_CANONICAL | XAUUSD | 0.01 | demo_order_executor | primary_xau_matrix_or_candidate_status |
| swing_breakout_retest_v0 | ACCEPTED | EXPERIMENTAL_QUARANTINE_REVIEW_ONLY | COST_SUSPENDED_CANONICAL | EURUSD | 0.05 | demo_order_executor | swing_breakout_retest_v0_multisymbol_summary.csv:PASS |
| swing_breakout_retest_v0 | ACCEPTED | EXPERIMENTAL_QUARANTINE_REVIEW_ONLY | COST_SUSPENDED_CANONICAL | GBPUSD | 0.01 | demo_order_executor | experimental_replacement_for_USDJPY:swing_breakout_retest_v0_multisymbol_summary.csv:PASS |
| swing_breakout_retest_v0 | ACCEPTED | EXPERIMENTAL_QUARANTINE_REVIEW_ONLY | COST_SUSPENDED_CANONICAL | XAUUSD | 0.01 | demo_order_executor | primary_xau_matrix_or_candidate_status |
| symbol_normalized_round_retest_v0 | ACCEPTED | EXPERIMENTAL_QUARANTINE_REVIEW_ONLY | COST_SUSPENDED_CANONICAL | EURUSD | 0.05 | demo_order_executor | symbol_normalized_round_retest_v0_multisymbol_summary.csv:PASS |
| symbol_normalized_round_retest_v0 | ACCEPTED | EXPERIMENTAL_QUARANTINE_REVIEW_ONLY | COST_SUSPENDED_CANONICAL | GBPUSD | 0.01 | demo_order_executor | experimental_replacement_for_USDJPY:symbol_normalized_round_retest_v0_multisymbol_summary.csv:PASS |
| symbol_normalized_round_retest_v0 | ACCEPTED | EXPERIMENTAL_QUARANTINE_REVIEW_ONLY | COST_SUSPENDED_CANONICAL | XAUUSD | 0.01 | demo_order_executor | primary_xau_matrix_or_candidate_status |
| round_number_retest_v0 | PROVISIONAL | EXPERIMENTAL_QUARANTINE_REVIEW_ONLY | COST_SUSPENDED_CANONICAL | GBPUSD | 0.01 | demo_order_executor | experimental_replacement_for_USDJPY:round_number_retest_v0_multisymbol_summary.csv:PASS |
| round_number_retest_v0 | PROVISIONAL | EXPERIMENTAL_QUARANTINE_REVIEW_ONLY | COST_SUSPENDED_CANONICAL | XAUUSD | 0.01 | demo_order_executor | primary_xau_matrix_or_candidate_status |
| session_extreme_retest_v0 | PROVISIONAL | EXPERIMENTAL_QUARANTINE_REVIEW_ONLY | COST_SUSPENDED_CANONICAL | EURUSD | 0.05 | demo_order_executor | session_extreme_retest_v0_multisymbol_summary.csv:PASS |
| session_extreme_retest_v0 | PROVISIONAL | EXPERIMENTAL_QUARANTINE_REVIEW_ONLY | COST_SUSPENDED_CANONICAL | GBPUSD | 0.01 | demo_order_executor | experimental_replacement_for_USDJPY:session_extreme_retest_v0_multisymbol_summary.csv:PASS |
| session_extreme_retest_v0 | PROVISIONAL | EXPERIMENTAL_QUARANTINE_REVIEW_ONLY | COST_SUSPENDED_CANONICAL | XAUUSD | 0.01 | demo_order_executor | primary_xau_matrix_or_candidate_status |

## Limitations

- All attachments must refuse live/real server names at EA startup.
- All attachments must refuse non-whitelisted account logins at EA startup.
- All attachments require the experimental authorization token; no token is written by default.
- All attachments require a separate cost-suspension acknowledgement token before startup.
- Same-family/provisional candidates require explicit inclusion in InpAuthorizedCandidatesCsv.
- A central kill-switch file named by InpKillSwitchFileName blocks new orders when it contains KILL.
- USDJPY is removed from this experimental demo portfolio and replaced by GBPUSD for measurement only; this is not canonical GBPUSD Phase 0 approval.
- Each candidate-symbol instance uses fixed 0.01 lot except EURUSD, which uses fixed 0.05 lot; hard SL/TP and one open exposure per instance still apply.
- Account-level daily order and open-position caps apply across chart instances.
- Current spread and estimated cost in R must remain below configured thresholds before any order is sent.
- This is an experimental demo execution run, not canonical live authorization.
