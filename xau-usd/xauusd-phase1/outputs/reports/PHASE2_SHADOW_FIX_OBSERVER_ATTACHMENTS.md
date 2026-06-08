# Phase 2 Shadow Fix Observer Attachments

Status: SHADOW_FIX_OBSERVERS_ATTACHED_TO_ISOLATED_TERMINAL

Shadow-fix observer setup only. Attachments log telemetry and explicitly set broker_action_allowed=false. This does not touch current demo trading EAs, does not place orders, and does not mark canonical Phase 2 as passed.

Run ID: `phase2-shadow-fix-observer-v0.1`
Attachment count: 14
Terminal: `C:\MT5PortableShadowFixObservers\terminal64.exe`
Data folder: `C:\MT5PortableShadowFixObservers`
Profile backup: `C:\MT5PortableShadowFixObservers\_codex_quarantine\profile_backups\default_profile_before_shadow_fix_attach_20260608_090702`
Observer log backup: `none`
Standard demo terminal touched: `False`
Standard demo terminal closed/restarted: `False`
Shadow policy: `shadow_fix_policy_20260608_v1`

| Candidate | Status | Symbol | Observer | Qualification |
|---|---|---|---|---|
| breakout_retest | ACCEPTED | EURUSD | native_signal_logger | breakout_retest_multisymbol_summary.csv:PASS |
| breakout_retest | ACCEPTED | USDJPY | native_signal_logger | breakout_retest_multisymbol_summary.csv:PASS |
| breakout_retest | ACCEPTED | XAUUSD | native_signal_logger | primary_xau_matrix_or_candidate_status |
| swing_breakout_retest_v0 | ACCEPTED | EURUSD | native_signal_logger | swing_breakout_retest_v0_multisymbol_summary.csv:PASS |
| swing_breakout_retest_v0 | ACCEPTED | USDJPY | native_signal_logger | swing_breakout_retest_v0_multisymbol_summary.csv:PASS |
| swing_breakout_retest_v0 | ACCEPTED | XAUUSD | native_signal_logger | primary_xau_matrix_or_candidate_status |
| symbol_normalized_round_retest_v0 | ACCEPTED | EURUSD | native_signal_logger | symbol_normalized_round_retest_v0_multisymbol_summary.csv:PASS |
| symbol_normalized_round_retest_v0 | ACCEPTED | USDJPY | native_signal_logger | symbol_normalized_round_retest_v0_multisymbol_summary.csv:PASS |
| symbol_normalized_round_retest_v0 | ACCEPTED | XAUUSD | native_signal_logger | primary_xau_matrix_or_candidate_status |
| round_number_retest_v0 | PROVISIONAL | USDJPY | native_signal_logger | round_number_retest_v0_multisymbol_summary.csv:PASS |
| round_number_retest_v0 | PROVISIONAL | XAUUSD | native_signal_logger | primary_xau_matrix_or_candidate_status |
| session_extreme_retest_v0 | PROVISIONAL | EURUSD | native_signal_logger | session_extreme_retest_v0_multisymbol_summary.csv:PASS |
| session_extreme_retest_v0 | PROVISIONAL | USDJPY | native_signal_logger | session_extreme_retest_v0_multisymbol_summary.csv:PASS |
| session_extreme_retest_v0 | PROVISIONAL | XAUUSD | native_signal_logger | primary_xau_matrix_or_candidate_status |

## Limitations

- Runs only in the isolated C:/MT5PortableShadowFixObservers terminal.
- The standard Capital.com demo trading terminal and its executor charts are not modified.
- All observers remain dry-run and explicitly set broker_action_allowed=false.
- Rows include shadow_action and shadow_reason for the proposed session/quarantine policy.
