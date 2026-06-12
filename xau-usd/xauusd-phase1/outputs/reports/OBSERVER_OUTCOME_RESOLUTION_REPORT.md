# Observer Outcome Resolution Report

Status: `PARTIAL_REVIEW_BARS_SUPPLIED`

Read-only outcome resolution for observer signals. It joins to exported broker trades and optionally replays SL/TP against supplied M5 bars. It does not touch MT5 runtime, orders, positions, profiles, charts, or running EAs.

Shadow files: `C:\MT5PortableShadowFixObservers\MQL5\Files`
Actual trades CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv`
Bars dir: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\m5_replay_bars`
Signals: `1283`
Broker trade rows: `1372`
Resolved rows: `1021`
Broker-joined rows: `77`
M5 replay rows: `944`
Unresolved rows: `262`
Scoreboard JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\OBSERVER_TREND_VETO_SCOREBOARD.json`
Scoreboard CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\OBSERVER_TREND_VETO_SCOREBOARD.csv`

## Notes

- Broker-trade join is the preferred proof when the demo EA actually took the same signal.
- M5 replay is only used when a bars_dir is provided and matching June 2026 bars exist.
- Replay uses adverse-first same-bar ordering, so if SL and TP are both touched in the same M5 bar the row is scored as SL.
- Rows without broker match or bars are left unresolved; no outcome is guessed.
- Observer LONG/SHORT directions are normalized to broker BUY/SELL only for matching and replay; the original direction is preserved.
- Proposed v2 shadow policy blocks the round-retest clone family: symbol_normalized_round_retest_v0 and round_number_retest_v0.

## By Resolution Status

| resolution_status | count |
| --- | --- |
| REPLAY_SL | 501 |
| REPLAY_TP | 443 |
| UNRESOLVED_REPLAY_NO_SL_TP_HIT | 262 |
| BROKER_CLOSED_LOSS | 51 |
| BROKER_CLOSED_WIN | 26 |

## By Resolution Source

| resolution_source | resolution_status | count |
| --- | --- | --- |
| m5_bar_replay_adverse_first | REPLAY_SL | 501 |
| m5_bar_replay_adverse_first | REPLAY_TP | 443 |
| m5_bar_replay_adverse_first | UNRESOLVED_REPLAY_NO_SL_TP_HIT | 262 |
| broker_trade_join | BROKER_CLOSED_LOSS | 51 |
| broker_trade_join | BROKER_CLOSED_WIN | 26 |

## By Proposed V2 Action

| proposed_v2_shadow_action | resolution_status | count |
| --- | --- | --- |
| BLOCK | REPLAY_SL | 425 |
| BLOCK | REPLAY_TP | 345 |
| KEEP | UNRESOLVED_REPLAY_NO_SL_TP_HIT | 173 |
| KEEP | REPLAY_TP | 98 |
| BLOCK | UNRESOLVED_REPLAY_NO_SL_TP_HIT | 89 |
| KEEP | REPLAY_SL | 76 |
| BLOCK | BROKER_CLOSED_LOSS | 51 |
| BLOCK | BROKER_CLOSED_WIN | 24 |
| KEEP | BROKER_CLOSED_WIN | 2 |

## By Candidate

| candidate | count |
| --- | --- |
| symbol_normalized_round_retest_v0 | 447 |
| round_number_retest_v0 | 357 |
| breakout_retest | 216 |
| swing_breakout_retest_v0 | 163 |
| session_extreme_retest_v0 | 100 |

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
