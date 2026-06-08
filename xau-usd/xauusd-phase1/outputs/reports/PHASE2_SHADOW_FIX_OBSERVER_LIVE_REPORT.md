# Phase 2 Shadow Fix Observer Live Report

Status: SHADOW_FIX_OBSERVER_LOGS_READY

Read-only summary of isolated shadow-fix observer logs. It does not touch MT5 runtime, orders, positions, charts, or the standard demo trading terminal.

Files dir: `C:\MT5PortableShadowFixObservers\MQL5\Files`
File count: `14`
Rows: `28`
Signals: `2`
Latest broker timestamp: `2026.06.08 09:10:00`

## Signal Actions

| shadow_action | count |
| --- | --- |
| KEEP | 1 |
| BLOCK | 1 |

## Signal Reasons

| shadow_reason | count |
| --- | --- |
| KEEP | 1 |
| BLOCK_WEAK_EA_SYMBOL_NORMALIZED_ROUND | 1 |

## Signal By Candidate

| candidate | count |
| --- | --- |
| round_number_retest_v0 | 1 |
| symbol_normalized_round_retest_v0 | 1 |

## Signal By Symbol

| symbol | count |
| --- | --- |
| USDJPY | 2 |

## Signal By Time Bucket

| time_bucket | count |
| --- | --- |
| Afternoon 12:00-15:59 | 2 |

## Signal By Candidate x Symbol x Time

| candidate | symbol | time_bucket | count |
| --- | --- | --- | --- |
| round_number_retest_v0 | USDJPY | Afternoon 12:00-15:59 | 1 |
| symbol_normalized_round_retest_v0 | USDJPY | Afternoon 12:00-15:59 | 1 |
