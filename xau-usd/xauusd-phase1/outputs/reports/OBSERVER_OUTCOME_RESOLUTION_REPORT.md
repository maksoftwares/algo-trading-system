# Observer Outcome Resolution Report

Status: `PARTIAL_REVIEW_BARS_SUPPLIED`

Read-only outcome resolution for observer signals. It joins to exported broker trades and optionally replays executor-faithful synthetic SL/TP against supplied M5 bars. It does not touch MT5 runtime, orders, positions, profiles, charts, or running EAs.

Shadow files: `C:\MT5PortableShadowFixObservers\MQL5\Files`
Actual trades CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv`
Bars dir: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\m5_replay_bars`
Replay model: `executor_v2`
Scoreboard mode: `broker_joined_only`
Signals: `1308`
Broker trade rows: `1372`
Resolved rows: `1007`
Broker-joined rows: `81`
M5 replay rows: `926`
Unresolved rows: `301`
Scoreboard JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\OBSERVER_SHADOW_POLICY_SCOREBOARD.json`
Scoreboard CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\OBSERVER_SHADOW_POLICY_SCOREBOARD.csv`

## Notes

- Broker-trade join is the preferred proof when the demo EA actually took the same signal.
- M5 replay is only used when a bars_dir is provided and matching June 2026 bars exist.
- Replay model executor_v2 simulates Phase2ExperimentalDemoExecutor.SendDemoMarketOrder: next-M5-open entry, measured spread adjustment, stop floor, synthetic SL/TP, and adverse-first same-bar exits.
- Replay uses adverse-first same-bar ordering, so if SL and TP are both touched in the same M5 bar the row is scored as SL.
- Rows without broker match or bars are left unresolved; no outcome is guessed.
- Observer LONG/SHORT directions are normalized to broker BUY/SELL only for matching and replay; the original direction is preserved.
- Replay rows include gross R, estimated cost R, and net R. v1 plan-replay columns are retained only for calibration diffing.
- Portfolio-level totals must use the family rollup because clone EAs can emit duplicate same-family signals.
- Proposed v2 shadow policy blocks the round-retest clone family: symbol_normalized_round_retest_v0 and round_number_retest_v0.

## By Resolution Status

| resolution_status | count |
| --- | --- |
| REPLAY_SL | 622 |
| REPLAY_TP | 304 |
| UNRESOLVED_REPLAY_NO_EXECUTOR_ENTRY_BAR | 281 |
| BROKER_CLOSED_LOSS | 55 |
| BROKER_CLOSED_WIN | 26 |
| UNRESOLVED_REPLAY_NO_SL_TP_HIT | 20 |

## By Resolution Source

| resolution_source | resolution_status | count |
| --- | --- | --- |
| m5_bar_replay_executor_v2_adverse_first | REPLAY_SL | 622 |
| m5_bar_replay_executor_v2_adverse_first | REPLAY_TP | 304 |
| m5_bar_replay_executor_v2_adverse_first | UNRESOLVED_REPLAY_NO_EXECUTOR_ENTRY_BAR | 281 |
| broker_trade_join | BROKER_CLOSED_LOSS | 55 |
| broker_trade_join | BROKER_CLOSED_WIN | 26 |
| m5_bar_replay_executor_v2_adverse_first | UNRESOLVED_REPLAY_NO_SL_TP_HIT | 20 |

## By Proposed V2 Action

| proposed_v2_shadow_action | resolution_status | count |
| --- | --- | --- |
| BLOCK | REPLAY_SL | 497 |
| BLOCK | REPLAY_TP | 259 |
| KEEP | UNRESOLVED_REPLAY_NO_EXECUTOR_ENTRY_BAR | 177 |
| KEEP | REPLAY_SL | 125 |
| BLOCK | UNRESOLVED_REPLAY_NO_EXECUTOR_ENTRY_BAR | 104 |
| BLOCK | BROKER_CLOSED_LOSS | 55 |
| KEEP | REPLAY_TP | 45 |
| BLOCK | BROKER_CLOSED_WIN | 24 |
| BLOCK | UNRESOLVED_REPLAY_NO_SL_TP_HIT | 18 |
| KEEP | BROKER_CLOSED_WIN | 2 |
| KEEP | UNRESOLVED_REPLAY_NO_SL_TP_HIT | 2 |

## By Candidate

| candidate | count |
| --- | --- |
| symbol_normalized_round_retest_v0 | 458 |
| round_number_retest_v0 | 368 |
| breakout_retest | 217 |
| swing_breakout_retest_v0 | 164 |
| session_extreme_retest_v0 | 101 |

## Bar Export Quality

| symbol | status | rows | first_bar | last_bar | continuity_pct | gap_count_gt_5m | duplicate_bar_times |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EURUSD | WARN_GAPS_OR_DUPLICATES | 2696 | 2026-06-01 00:00:00 | 2026-06-12 09:15:00 | 82.20 | 9 | 0 |
| USDJPY | WARN_GAPS_OR_DUPLICATES | 1611 | 2026-06-01 00:00:00 | 2026-06-08 14:30:00 | 73.53 | 5 | 0 |
| XAUUSD | WARN_GAPS_OR_DUPLICATES | 2596 | 2026-06-01 00:00:00 | 2026-06-12 09:15:00 | 79.15 | 9 | 0 |

## Boundary

- This is analysis-only.
- It does not modify MT5 runtime or running EAs.
- Rows without broker match or fresh M5 bars remain unresolved.
