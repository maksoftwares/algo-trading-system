# Phase 2 GBPUSD Replacement Report

Status: `PASS`

Standard Capital.com demo terminal Phase2ExperimentalDemoExecutor attachments only; Phase2X isolated owner terminal untouched.

Requested change: Remove USDJPY from experimental demo portfolio and replace the same slots with GBPUSD.
Terminal: `C:\Program Files\MetaTrader 5\terminal64.exe`
Data folder: `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075`
Profile backup: `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\_codex_quarantine\profile_backups\default_profile_before_demo_attach_20260608_124303`
WR50 charts restored from: `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\_codex_quarantine\profile_backups\default_profile_before_eurusd_lot_update_20260608_122634`
Compile log: `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Logs\compile_Phase2ExperimentalDemoExecutor.log`
Executor charts: `14`
GBPUSD charts active: `5`
USDJPY executor charts active: `0`
EURUSD charts active: `4`
XAUUSD charts active: `5`

Existing USDJPY broker positions were not closed by this change; only new USDJPY executor entries are disabled by removing USDJPY charts.

| Candidate | Symbol | Lot | Qualification |
|---|---|---:|---|
| breakout_retest | EURUSD | 0.05 | breakout_retest_multisymbol_summary.csv:PASS |
| breakout_retest | GBPUSD | 0.01 | experimental_replacement_for_USDJPY:breakout_retest_multisymbol_summary.csv:PASS |
| breakout_retest | XAUUSD | 0.01 | primary_xau_matrix_or_candidate_status |
| swing_breakout_retest_v0 | EURUSD | 0.05 | swing_breakout_retest_v0_multisymbol_summary.csv:PASS |
| swing_breakout_retest_v0 | GBPUSD | 0.01 | experimental_replacement_for_USDJPY:swing_breakout_retest_v0_multisymbol_summary.csv:PASS |
| swing_breakout_retest_v0 | XAUUSD | 0.01 | primary_xau_matrix_or_candidate_status |
| symbol_normalized_round_retest_v0 | EURUSD | 0.05 | symbol_normalized_round_retest_v0_multisymbol_summary.csv:PASS |
| symbol_normalized_round_retest_v0 | GBPUSD | 0.01 | experimental_replacement_for_USDJPY:symbol_normalized_round_retest_v0_multisymbol_summary.csv:PASS |
| symbol_normalized_round_retest_v0 | XAUUSD | 0.01 | primary_xau_matrix_or_candidate_status |
| round_number_retest_v0 | GBPUSD | 0.01 | experimental_replacement_for_USDJPY:round_number_retest_v0_multisymbol_summary.csv:PASS |
| round_number_retest_v0 | XAUUSD | 0.01 | primary_xau_matrix_or_candidate_status |
| session_extreme_retest_v0 | EURUSD | 0.05 | session_extreme_retest_v0_multisymbol_summary.csv:PASS |
| session_extreme_retest_v0 | GBPUSD | 0.01 | experimental_replacement_for_USDJPY:session_extreme_retest_v0_multisymbol_summary.csv:PASS |
| session_extreme_retest_v0 | XAUUSD | 0.01 | primary_xau_matrix_or_candidate_status |
