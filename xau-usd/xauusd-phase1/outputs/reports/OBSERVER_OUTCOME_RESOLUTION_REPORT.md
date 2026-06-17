# Observer Outcome Resolution Report

Status: `PARTIAL_REVIEW_BARS_SUPPLIED`

Read-only outcome resolution for observer signals. It joins to exported broker trades and optionally replays executor-faithful synthetic SL/TP against supplied M5 bars. It does not touch MT5 runtime, orders, positions, profiles, charts, or running EAs.

Shadow files: `C:\MT5PortableShadowFixObservers\MQL5\Files`
Actual trades CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv`
Bars dir: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\m5_replay_bars`
Replay model: `executor_v2`
Scoreboard mode: `broker_joined_only`
Signals: `1775`
Broker trade rows: `1696`
Resolved rows: `1657`
Broker-joined rows: `105`
M5 replay rows: `1552`
Unresolved rows: `118`
Scoreboard JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\OBSERVER_SHADOW_POLICY_SCOREBOARD.json`
Scoreboard CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\OBSERVER_SHADOW_POLICY_SCOREBOARD.csv`

## Notes

- Broker-trade join is the preferred proof when the demo EA actually took the same signal.
- Rows with evidence_tier=BROKER use actual broker state, profit, and exit data as the authoritative outcome.
- Rows with evidence_tier=REPLAY are secondary reference evidence only; broker-tier scoreboards should be used for current decisions.
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
| REPLAY_SL | 1030 |
| REPLAY_TP | 522 |
| UNRESOLVED_REPLAY_NO_EXECUTOR_ENTRY_BAR | 77 |
| BROKER_CLOSED_LOSS | 74 |
| UNRESOLVED_REPLAY_NO_SL_TP_HIT | 41 |
| BROKER_CLOSED_WIN | 31 |

## By Evidence Tier

| evidence_tier | resolution_status | count |
| --- | --- | --- |
| REPLAY | REPLAY_SL | 1030 |
| REPLAY | REPLAY_TP | 522 |
| UNKNOWN | UNRESOLVED_REPLAY_NO_EXECUTOR_ENTRY_BAR | 77 |
| BROKER | BROKER_CLOSED_LOSS | 74 |
| UNKNOWN | UNRESOLVED_REPLAY_NO_SL_TP_HIT | 41 |
| BROKER | BROKER_CLOSED_WIN | 31 |

## By Resolution Source

| resolution_source | resolution_status | count |
| --- | --- | --- |
| m5_bar_replay_executor_v2_adverse_first | REPLAY_SL | 1030 |
| m5_bar_replay_executor_v2_adverse_first | REPLAY_TP | 522 |
| m5_bar_replay_executor_v2_adverse_first | UNRESOLVED_REPLAY_NO_EXECUTOR_ENTRY_BAR | 77 |
| broker_trade_join | BROKER_CLOSED_LOSS | 74 |
| m5_bar_replay_executor_v2_adverse_first | UNRESOLVED_REPLAY_NO_SL_TP_HIT | 41 |
| broker_trade_join | BROKER_CLOSED_WIN | 31 |

## Broker-Fill Scoreboards

These tables use only `evidence_tier=BROKER` rows. They are the authoritative observer outcome view.

### By Session

| group | rows | closed | wins | losses | open | flat | win_rate_pct | broker_profit_aed | replay_net_r_sum |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Afternoon 12:00-15:59 | 20 | 20 | 0 | 20 | 0 | 0 | 0.00 | -461.46 |  |
| Evening 16:00-19:59 | 13 | 13 | 4 | 9 | 0 | 0 | 30.77 | 110.28 |  |
| Morning 06:00-11:59 | 27 | 27 | 7 | 20 | 0 | 0 | 25.93 | -409.18 |  |
| Night 20:00-05:59 | 45 | 45 | 20 | 25 | 0 | 0 | 44.44 | 368.66 |  |

### By Cost Bucket

| group | rows | closed | wins | losses | open | flat | win_rate_pct | broker_profit_aed | replay_net_r_sum |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| HIGH_51_75pt | 32 | 32 | 8 | 24 | 0 | 0 | 25.00 | -370.97 |  |
| LOW_<=30pt | 2 | 2 | 2 | 0 | 0 | 0 | 100.00 | 55.72 |  |
| MEDIUM_31_50pt | 71 | 71 | 21 | 50 | 0 | 0 | 29.58 | -76.45 |  |

### By Direction

| group | rows | closed | wins | losses | open | flat | win_rate_pct | broker_profit_aed | replay_net_r_sum |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BUY | 36 | 36 | 6 | 30 | 0 | 0 | 16.67 | -443.93 |  |
| SELL | 69 | 69 | 25 | 44 | 0 | 0 | 36.23 | 52.23 |  |

### By Regime

| group | rows | closed | wins | losses | open | flat | win_rate_pct | broker_profit_aed | replay_net_r_sum |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| WOULD_SIGNAL | 105 | 105 | 31 | 74 | 0 | 0 | 29.52 | -391.70 |  |

### By Family

| group | rows | closed | wins | losses | open | flat | win_rate_pct | broker_profit_aed | replay_net_r_sum |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| breakout | 2 | 2 | 2 | 0 | 0 | 0 | 100.00 | 55.72 |  |
| round | 103 | 103 | 29 | 74 | 0 | 0 | 28.16 | -447.42 |  |

### By Lane

| group | rows | closed | wins | losses | open | flat | win_rate_pct | broker_profit_aed | replay_net_r_sum |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| accepted_round_family | 103 | 103 | 29 | 74 | 0 | 0 | 28.16 | -447.42 |  |
| accepted_same_family | 2 | 2 | 2 | 0 | 0 | 0 | 100.00 | 55.72 |  |

### By EA / Symbol / Session

| group | rows | closed | wins | losses | open | flat | win_rate_pct | broker_profit_aed | replay_net_r_sum |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| breakout_retest | EURUSD | Night 20:00-05:59 | 1 | 1 | 1 | 0 | 0 | 0 | 100.00 | 27.86 |  |
| round_number_retest_v0 | XAUUSD | Afternoon 12:00-15:59 | 9 | 9 | 0 | 9 | 0 | 0 | 0.00 | -206.10 |  |
| round_number_retest_v0 | XAUUSD | Evening 16:00-19:59 | 6 | 6 | 2 | 4 | 0 | 0 | 33.33 | 57.83 |  |
| round_number_retest_v0 | XAUUSD | Morning 06:00-11:59 | 13 | 13 | 3 | 10 | 0 | 0 | 23.08 | -235.13 |  |
| round_number_retest_v0 | XAUUSD | Night 20:00-05:59 | 21 | 21 | 9 | 12 | 0 | 0 | 42.86 | 167.62 |  |
| swing_breakout_retest_v0 | EURUSD | Night 20:00-05:59 | 1 | 1 | 1 | 0 | 0 | 0 | 100.00 | 27.86 |  |
| symbol_normalized_round_retest_v0 | XAUUSD | Afternoon 12:00-15:59 | 11 | 11 | 0 | 11 | 0 | 0 | 0.00 | -255.36 |  |
| symbol_normalized_round_retest_v0 | XAUUSD | Evening 16:00-19:59 | 7 | 7 | 2 | 5 | 0 | 0 | 28.57 | 52.45 |  |
| symbol_normalized_round_retest_v0 | XAUUSD | Morning 06:00-11:59 | 14 | 14 | 4 | 10 | 0 | 0 | 28.57 | -174.05 |  |
| symbol_normalized_round_retest_v0 | XAUUSD | Night 20:00-05:59 | 22 | 22 | 9 | 13 | 0 | 0 | 40.91 | 145.32 |  |

## Replay Reference Scoreboards

These tables use only `evidence_tier=REPLAY` rows. Treat them as secondary reference evidence.

### Replay By Session

| group | rows | closed | wins | losses | open | flat | win_rate_pct | broker_profit_aed | replay_net_r_sum |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Afternoon 12:00-15:59 | 251 | 251 | 86 | 165 | 0 | 0 | 34.26 | 0.00 | -65.8878 |
| Evening 16:00-19:59 | 361 | 361 | 140 | 221 | 0 | 0 | 38.78 | 0.00 | -41.7565 |
| Morning 06:00-11:59 | 317 | 317 | 106 | 211 | 0 | 0 | 33.44 | 0.00 | -92.0414 |
| Night 20:00-05:59 | 623 | 623 | 190 | 433 | 0 | 0 | 30.50 | 0.00 | -220.9879 |

## By Proposed V2 Action

| proposed_v2_shadow_action | resolution_status | count |
| --- | --- | --- |
| BLOCK | REPLAY_SL | 718 |
| BLOCK | REPLAY_TP | 391 |
| KEEP | REPLAY_SL | 312 |
| KEEP | REPLAY_TP | 131 |
| BLOCK | BROKER_CLOSED_LOSS | 74 |
| KEEP | UNRESOLVED_REPLAY_NO_EXECUTOR_ENTRY_BAR | 60 |
| KEEP | UNRESOLVED_REPLAY_NO_SL_TP_HIT | 32 |
| BLOCK | BROKER_CLOSED_WIN | 29 |
| BLOCK | UNRESOLVED_REPLAY_NO_EXECUTOR_ENTRY_BAR | 17 |
| BLOCK | UNRESOLVED_REPLAY_NO_SL_TP_HIT | 9 |
| KEEP | BROKER_CLOSED_WIN | 2 |

## By Candidate

| candidate | count |
| --- | --- |
| symbol_normalized_round_retest_v0 | 591 |
| round_number_retest_v0 | 481 |
| breakout_retest | 327 |
| swing_breakout_retest_v0 | 247 |
| session_extreme_retest_v0 | 129 |

## Bar Export Quality

| symbol | status | rows | first_bar | last_bar | continuity_pct | gap_count_gt_5m | duplicate_bar_times |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EURUSD | WARN_GAPS_OR_DUPLICATES | 3240 | 2026-06-01 00:00:00 | 2026-06-16 06:40:00 | 73.62 | 11 | 0 |
| USDJPY | WARN_GAPS_OR_DUPLICATES | 2836 | 2026-06-01 00:00:00 | 2026-06-12 20:55:00 | 82.92 | 9 | 0 |
| XAUUSD | WARN_GAPS_OR_DUPLICATES | 3117 | 2026-06-01 00:00:00 | 2026-06-16 06:40:00 | 70.82 | 11 | 0 |

## Boundary

- This is analysis-only.
- It does not modify MT5 runtime or running EAs.
- Rows without broker match or fresh M5 bars remain unresolved.
