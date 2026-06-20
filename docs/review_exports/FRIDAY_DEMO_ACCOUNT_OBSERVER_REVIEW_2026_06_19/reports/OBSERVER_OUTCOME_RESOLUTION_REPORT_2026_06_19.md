# Observer Outcome Resolution Report

Status: `PARTIAL_REVIEW_NEEDS_FRESH_M5_BARS`

Read-only outcome resolution for observer signals. It joins to exported broker trades and optionally replays executor-faithful synthetic SL/TP against supplied M5 bars. It does not touch MT5 runtime, orders, positions, profiles, charts, or running EAs.

Shadow files: `C:\MT5PortableShadowFixObservers\MQL5\Files`
Actual trades CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\EOD_GOLD_OBSERVER_JOIN_INPUT_20260619.csv`
Bars dir: `not supplied`
Replay model: `executor_v2`
Scoreboard mode: `broker_joined_only`
Signals: `2643`
Broker trade rows: `5`
Resolved rows: `2`
Broker-joined rows: `2`
M5 replay rows: `0`
Unresolved rows: `2641`
Scoreboard JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\OBSERVER_SHADOW_POLICY_SCOREBOARD_2026_06_19.json`
Scoreboard CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\OBSERVER_SHADOW_POLICY_SCOREBOARD_2026_06_19.csv`

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
| UNRESOLVED_NO_BROKER_MATCH_NO_REPLAY_BARS | 2641 |
| BROKER_CLOSED_LOSS | 2 |

## By Evidence Tier

| evidence_tier | resolution_status | count |
| --- | --- | --- |
| UNKNOWN | UNRESOLVED_NO_BROKER_MATCH_NO_REPLAY_BARS | 2641 |
| BROKER | BROKER_CLOSED_LOSS | 2 |

## By Resolution Source

| resolution_source | resolution_status | count |
| --- | --- | --- |
| UNKNOWN | UNRESOLVED_NO_BROKER_MATCH_NO_REPLAY_BARS | 2641 |
| broker_trade_join | BROKER_CLOSED_LOSS | 2 |

## Broker-Fill Scoreboards

These tables use only `evidence_tier=BROKER` rows. They are the authoritative observer outcome view.

### By Session

| group | rows | closed | wins | losses | open | flat | win_rate_pct | broker_profit_aed | replay_net_r_sum |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Evening 16:00-19:59 | 2 | 2 | 0 | 2 | 0 | 0 | 0.00 | -23.47 |  |

### By Cost Bucket

| group | rows | closed | wins | losses | open | flat | win_rate_pct | broker_profit_aed | replay_net_r_sum |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MEDIUM_31_50pt | 2 | 2 | 0 | 2 | 0 | 0 | 0.00 | -23.47 |  |

### By Direction

| group | rows | closed | wins | losses | open | flat | win_rate_pct | broker_profit_aed | replay_net_r_sum |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BUY | 2 | 2 | 0 | 2 | 0 | 0 | 0.00 | -23.47 |  |

### By Regime

| group | rows | closed | wins | losses | open | flat | win_rate_pct | broker_profit_aed | replay_net_r_sum |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| WOULD_SIGNAL | 2 | 2 | 0 | 2 | 0 | 0 | 0.00 | -23.47 |  |

### By Family

| group | rows | closed | wins | losses | open | flat | win_rate_pct | broker_profit_aed | replay_net_r_sum |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| breakout | 2 | 2 | 0 | 2 | 0 | 0 | 0.00 | -23.47 |  |

### By Lane

| group | rows | closed | wins | losses | open | flat | win_rate_pct | broker_profit_aed | replay_net_r_sum |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| accepted_same_family | 2 | 2 | 0 | 2 | 0 | 0 | 0.00 | -23.47 |  |

### By EA / Symbol / Session

| group | rows | closed | wins | losses | open | flat | win_rate_pct | broker_profit_aed | replay_net_r_sum |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| breakout_retest | XAUUSD | Evening 16:00-19:59 | 2 | 2 | 0 | 2 | 0 | 0 | 0.00 | -23.47 |  |

## Replay Reference Scoreboards

These tables use only `evidence_tier=REPLAY` rows. Treat them as secondary reference evidence.

### Replay By Session

_No rows._

## By Proposed V2 Action

| proposed_v2_shadow_action | resolution_status | count |
| --- | --- | --- |
| BLOCK | UNRESOLVED_NO_BROKER_MATCH_NO_REPLAY_BARS | 1788 |
| KEEP | UNRESOLVED_NO_BROKER_MATCH_NO_REPLAY_BARS | 853 |
| KEEP | BROKER_CLOSED_LOSS | 2 |

## By Candidate

| candidate | count |
| --- | --- |
| symbol_normalized_round_retest_v0 | 832 |
| round_number_retest_v0 | 684 |
| breakout_retest | 529 |
| swing_breakout_retest_v0 | 399 |
| session_extreme_retest_v0 | 199 |

## Bar Export Quality

_No rows._

## Boundary

- This is analysis-only.
- It does not modify MT5 runtime or running EAs.
- Rows without broker match or fresh M5 bars remain unresolved.
