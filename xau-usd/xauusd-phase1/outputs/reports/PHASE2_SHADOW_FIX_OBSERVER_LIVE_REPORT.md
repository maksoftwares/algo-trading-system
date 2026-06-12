# Phase 2 Shadow Fix Observer Live Report

Status: SHADOW_FIX_OBSERVER_LOGS_READY

Read-only summary of isolated shadow-fix observer logs. It does not touch MT5 runtime, orders, positions, charts, or the standard demo trading terminal.

Files dir: `C:\MT5PortableShadowFixObservers\MQL5\Files`
File count: `14`
Rows: `15586`
Signals: `1253`
Latest broker timestamp: `2026.06.12 07:21:50`

## Signal Actions

| shadow_action | count |
| --- | --- |
| BLOCK | 688 |
| KEEP | 565 |

## Signal Reasons

| shadow_reason | count |
| --- | --- |
| KEEP | 565 |
| BLOCK_WEAK_EA_SYMBOL_NORMALIZED_ROUND | 438 |
| BLOCK_XAUUSD_MORNING_AFTERNOON | 152 |
| BLOCK_WEAK_EA_SESSION_EXTREME_RETEST | 96 |
| BLOCK_WEAK_EA_ROUND_RETEST_CLONE_FAMILY | 2 |

## Signal By Candidate

| candidate | count |
| --- | --- |
| symbol_normalized_round_retest_v0 | 439 |
| round_number_retest_v0 | 349 |
| breakout_retest | 209 |
| swing_breakout_retest_v0 | 160 |
| session_extreme_retest_v0 | 96 |

## Signal By Symbol

| symbol | count |
| --- | --- |
| XAUUSD | 777 |
| USDJPY | 264 |
| EURUSD | 212 |

## Signal By Time Bucket

| time_bucket | count |
| --- | --- |
| Night 20:00-05:59 | 523 |
| Evening 16:00-19:59 | 288 |
| Morning 06:00-11:59 | 253 |
| Afternoon 12:00-15:59 | 189 |

## Signal By Candidate x Symbol x Time

| candidate | symbol | time_bucket | count |
| --- | --- | --- | --- |
| round_number_retest_v0 | XAUUSD | Night 20:00-05:59 | 132 |
| symbol_normalized_round_retest_v0 | XAUUSD | Night 20:00-05:59 | 132 |
| round_number_retest_v0 | XAUUSD | Evening 16:00-19:59 | 80 |
| symbol_normalized_round_retest_v0 | XAUUSD | Evening 16:00-19:59 | 80 |
| round_number_retest_v0 | XAUUSD | Morning 06:00-11:59 | 76 |
| symbol_normalized_round_retest_v0 | XAUUSD | Morning 06:00-11:59 | 76 |
| breakout_retest | USDJPY | Night 20:00-05:59 | 54 |
| round_number_retest_v0 | XAUUSD | Afternoon 12:00-15:59 | 47 |
| symbol_normalized_round_retest_v0 | XAUUSD | Afternoon 12:00-15:59 | 47 |
| swing_breakout_retest_v0 | USDJPY | Night 20:00-05:59 | 35 |
| breakout_retest | EURUSD | Night 20:00-05:59 | 23 |
| session_extreme_retest_v0 | EURUSD | Evening 16:00-19:59 | 22 |
| session_extreme_retest_v0 | USDJPY | Night 20:00-05:59 | 22 |
| symbol_normalized_round_retest_v0 | EURUSD | Night 20:00-05:59 | 22 |
| symbol_normalized_round_retest_v0 | USDJPY | Night 20:00-05:59 | 22 |
| breakout_retest | USDJPY | Morning 06:00-11:59 | 20 |
| session_extreme_retest_v0 | EURUSD | Night 20:00-05:59 | 20 |
| swing_breakout_retest_v0 | EURUSD | Night 20:00-05:59 | 20 |
| breakout_retest | EURUSD | Afternoon 12:00-15:59 | 18 |
| breakout_retest | USDJPY | Evening 16:00-19:59 | 18 |
| breakout_retest | XAUUSD | Night 20:00-05:59 | 16 |
| symbol_normalized_round_retest_v0 | USDJPY | Morning 06:00-11:59 | 15 |
| breakout_retest | EURUSD | Evening 16:00-19:59 | 14 |
| swing_breakout_retest_v0 | XAUUSD | Night 20:00-05:59 | 14 |
| swing_breakout_retest_v0 | EURUSD | Afternoon 12:00-15:59 | 13 |
| swing_breakout_retest_v0 | USDJPY | Morning 06:00-11:59 | 13 |
| symbol_normalized_round_retest_v0 | USDJPY | Afternoon 12:00-15:59 | 13 |
| breakout_retest | EURUSD | Morning 06:00-11:59 | 12 |
| session_extreme_retest_v0 | XAUUSD | Evening 16:00-19:59 | 12 |
| swing_breakout_retest_v0 | EURUSD | Morning 06:00-11:59 | 12 |
| swing_breakout_retest_v0 | USDJPY | Evening 16:00-19:59 | 12 |
| breakout_retest | XAUUSD | Evening 16:00-19:59 | 11 |
| swing_breakout_retest_v0 | XAUUSD | Evening 16:00-19:59 | 11 |
| symbol_normalized_round_retest_v0 | EURUSD | Morning 06:00-11:59 | 11 |
| breakout_retest | XAUUSD | Morning 06:00-11:59 | 10 |
| swing_breakout_retest_v0 | EURUSD | Evening 16:00-19:59 | 10 |
| symbol_normalized_round_retest_v0 | USDJPY | Evening 16:00-19:59 | 10 |
| round_number_retest_v0 | USDJPY | Afternoon 12:00-15:59 | 8 |
| swing_breakout_retest_v0 | XAUUSD | Morning 06:00-11:59 | 8 |
| breakout_retest | USDJPY | Afternoon 12:00-15:59 | 7 |
| session_extreme_retest_v0 | XAUUSD | Afternoon 12:00-15:59 | 7 |
| symbol_normalized_round_retest_v0 | EURUSD | Afternoon 12:00-15:59 | 7 |
| breakout_retest | XAUUSD | Afternoon 12:00-15:59 | 6 |
| session_extreme_retest_v0 | XAUUSD | Night 20:00-05:59 | 6 |
| swing_breakout_retest_v0 | USDJPY | Afternoon 12:00-15:59 | 6 |
| swing_breakout_retest_v0 | XAUUSD | Afternoon 12:00-15:59 | 6 |
| round_number_retest_v0 | USDJPY | Night 20:00-05:59 | 5 |
| session_extreme_retest_v0 | EURUSD | Afternoon 12:00-15:59 | 4 |
| symbol_normalized_round_retest_v0 | EURUSD | Evening 16:00-19:59 | 4 |
| session_extreme_retest_v0 | USDJPY | Evening 16:00-19:59 | 3 |
| round_number_retest_v0 | USDJPY | Evening 16:00-19:59 | 1 |
