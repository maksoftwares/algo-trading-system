# Observer Outcome Resolution Report

Status: `PARTIAL_REVIEW_BARS_SUPPLIED`

Read-only outcome resolution for observer signals. It joins to exported broker trades and optionally replays executor-faithful synthetic SL/TP against supplied M5 bars. It does not touch MT5 runtime, orders, positions, profiles, charts, or running EAs.

Shadow files: `C:\MT5PortableTrendGuardedFixObservers\MQL5\Files`
Actual trades CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv`
Bars dir: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\m5_replay_bars`
Replay model: `executor_v2`
Scoreboard mode: `broker_joined_only`
Signals: `45`
Broker trade rows: `1372`
Resolved rows: `4`
Broker-joined rows: `4`
M5 replay rows: `0`
Unresolved rows: `41`
Scoreboard JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\TREND_VETO_LANE_SCOREBOARD.json`
Scoreboard CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\TREND_VETO_LANE_SCOREBOARD.csv`

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
| UNRESOLVED_REPLAY_NO_EXECUTOR_ENTRY_BAR | 25 |
| UNRESOLVED_REPLAY_NO_SL_TP_HIT | 16 |
| BROKER_CLOSED_LOSS | 4 |

## By Resolution Source

| resolution_source | resolution_status | count |
| --- | --- | --- |
| m5_bar_replay_executor_v2_adverse_first | UNRESOLVED_REPLAY_NO_EXECUTOR_ENTRY_BAR | 25 |
| m5_bar_replay_executor_v2_adverse_first | UNRESOLVED_REPLAY_NO_SL_TP_HIT | 16 |
| broker_trade_join | BROKER_CLOSED_LOSS | 4 |

## By Proposed V2 Action

| proposed_v2_shadow_action | resolution_status | count |
| --- | --- | --- |
| BLOCK | UNRESOLVED_REPLAY_NO_EXECUTOR_ENTRY_BAR | 18 |
| BLOCK | UNRESOLVED_REPLAY_NO_SL_TP_HIT | 10 |
| KEEP | UNRESOLVED_REPLAY_NO_EXECUTOR_ENTRY_BAR | 7 |
| KEEP | UNRESOLVED_REPLAY_NO_SL_TP_HIT | 6 |
| BLOCK | BROKER_CLOSED_LOSS | 4 |

## By Candidate

| candidate | count |
| --- | --- |
| symbol_normalized_round_retest_v0 | 14 |
| round_number_retest_v0 | 12 |
| session_extreme_retest_v0 | 6 |
| breakout_retest | 5 |
| swing_breakout_retest_v0 | 5 |
| session_extreme_retest_v0_repair_v1 | 3 |

## Bar Export Quality

| symbol | status | rows | first_bar | last_bar | continuity_pct | gap_count_gt_5m | duplicate_bar_times |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EURUSD | WARN_GAPS_OR_DUPLICATES | 2696 | 2026-06-01 00:00:00 | 2026-06-12 09:15:00 | 82.20 | 9 | 0 |
| GBPUSD | WARN_GAPS_OR_DUPLICATES | 2696 | 2026-06-01 00:00:00 | 2026-06-12 09:15:00 | 82.20 | 9 | 0 |
| XAUUSD | WARN_GAPS_OR_DUPLICATES | 2596 | 2026-06-01 00:00:00 | 2026-06-12 09:15:00 | 79.15 | 9 | 0 |

## Boundary

- This is analysis-only.
- It does not modify MT5 runtime or running EAs.
- Rows without broker match or fresh M5 bars remain unresolved.
