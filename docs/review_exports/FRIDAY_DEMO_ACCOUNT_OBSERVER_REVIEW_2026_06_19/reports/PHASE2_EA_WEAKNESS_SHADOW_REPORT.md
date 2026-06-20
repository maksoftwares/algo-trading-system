# Phase 2 EA Weakness Shadow Report

Status: SHADOW_ONLY_NOT_ENFORCED

Measurement only. Does not change MT5 charts, EA inputs, orders, positions, presets, or runtime behavior.

Generated at UTC: `2026-06-19T19:32:34.064204Z`
History window: `2026-06-01 00:00:00` to `2026-06-19 23:32:33`
Account: `1025742` / `Capital.ComMena-Demo` / `AED`

## Policy Under Measurement

- Use duplicate-hidden actual trades as the main decision view.
- Measure one-event-per-family duplicate mutex.
- Keep duplicate priority: breakout_retest, swing_breakout_retest_v0, then non-round provisional/experimental EAs.
- Measure family-level quarantine for symbol_normalized_round_retest_v0 and round_number_retest_v0 as the round-retest clone family.
- Measure separate EA quarantine for session_extreme_retest_v0.
- Measure XAUUSD morning/afternoon session block.
- Promote only after owner/reviewer approval and at least one fresh forward week.

## Main Decision Views

| View | Trades | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | Floating AED | Total AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Raw broker trades | 2059 | 2059 | 0 | 715 | 1274 | 34.73% | -2966.81 | 0.00 | -2966.81 | 0.90 | 38.05 | -23.68 |
| Duplicate-hidden decision view | 1298 | 1298 | 0 | 427 | 820 | 32.90% | -3141.76 | 0.00 | -3141.76 | 0.82 | 32.54 | -20.78 |
| Combined shadow would keep | 460 | 460 | 0 | 144 | 287 | 31.30% | -782.32 | 0.00 | -782.32 | 0.82 | 24.97 | -15.26 |
| Combined shadow would block | 838 | 838 | 0 | 283 | 533 | 33.77% | -2359.44 | 0.00 | -2359.44 | 0.81 | 36.39 | -23.75 |

## Shadow Scenarios

| Scenario | Baseline Closed | Kept Closed | Kept % | Delta PnL AED | Kept PF | Kept Win Rate | Promotion Status |
|---|---:|---:|---:|---:|---:|---:|---|
| Duplicate family mutex | 2059 | 1298 | 63.04% | -174.95 | 0.82 | 32.90% | REJECT_OR_KEEP_MEASURING |
| EA quarantine: session_extreme_retest_v0 | 1298 | 1156 | 89.06% | 184.15 | 0.81 | 33.22% | REJECT_OR_KEEP_MEASURING |
| EA quarantine: symbol_normalized_round_retest_v0 | 1298 | 693 | 53.39% | 2115.57 | 0.85 | 31.89% | REJECT_OR_KEEP_MEASURING |
| EA quarantine: round_number_retest_v0 | 1298 | 1258 | 96.92% | -16.86 | 0.81 | 32.59% | REJECT_OR_KEEP_MEASURING |
| Family quarantine: round-retest clone family | 1298 | 653 | 50.31% | 2098.71 | 0.83 | 31.24% | REJECT_OR_KEEP_MEASURING |
| Session filter: XAUUSD morning/afternoon | 1298 | 1023 | 78.81% | 1105.69 | 0.84 | 33.33% | SHADOW_CANDIDATE_NEEDS_FORWARD_WEEK |
| Combined proposed shadow policy | 1298 | 460 | 35.44% | 2359.44 | 0.82 | 31.30% | REJECT_OR_KEEP_MEASURING |

## Block Reason Counts

| Reason | Count |
|---|---:|
| BLOCK_WEAK_EA_ROUND_RETEST_CLONE_FAMILY | 645 |
| BLOCK_WEAK_EA_SESSION_EXTREME_RETEST | 142 |
| BLOCK_XAUUSD_MORNING_AFTERNOON | 51 |

## Duplicate-Hidden By EA

| candidate | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| round_number_retest_v0 | 40 | 0 | 17 | 23 | 42.50% | 16.86 | 1.04 | 28.29 | -20.17 |
| session_extreme_retest_v0_repair_v1 | 2 | 0 | 0 | 0 | 0.00% | 0.00 | n/a | n/a | n/a |
| p2weakness_br_v1 | 1 | 0 | 0 | 1 | 0.00% | -14.44 | 0.00 | n/a | -14.44 |
| symbol_normalized_round_retest_v0_repair_v1 | 13 | 0 | 1 | 5 | 7.69% | -54.83 | 0.53 | 62.71 | -23.51 |
| WR50_BreakoutEvening_v0 | 2 | 0 | 0 | 2 | 0.00% | -74.00 | 0.00 | n/a | -37.00 |
| session_extreme_retest_v0 | 142 | 0 | 43 | 87 | 30.28% | -184.15 | 0.85 | 25.14 | -14.54 |
| breakout_retest | 401 | 0 | 141 | 244 | 35.16% | -357.32 | 0.91 | 26.24 | -16.63 |
| swing_breakout_retest_v0 | 92 | 0 | 19 | 69 | 20.65% | -358.31 | 0.51 | 19.65 | -10.60 |
| symbol_normalized_round_retest_v0 | 605 | 0 | 206 | 389 | 34.05% | -2115.57 | 0.79 | 39.80 | -26.51 |

## Duplicate-Hidden By Symbol

| symbol | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| USDJPY | 21 | 0 | 4 | 16 | 19.05% | -24.94 | 0.45 | 5.14 | -2.84 |
| BTCUSD | 40 | 0 | 13 | 26 | 32.50% | -43.39 | 0.71 | 8.30 | -5.82 |
| EURUSD | 296 | 0 | 97 | 184 | 32.77% | -827.56 | 0.63 | 14.80 | -12.30 |
| XAUUSD | 712 | 0 | 261 | 437 | 36.66% | -942.13 | 0.92 | 42.73 | -27.67 |
| GBPUSD | 229 | 0 | 52 | 157 | 22.71% | -1303.74 | 0.48 | 22.70 | -15.82 |

## Duplicate-Hidden By Time Bucket

| time_bucket | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Evening 16:00-19:59 | 319 | 0 | 108 | 182 | 33.86% | -43.29 | 0.99 | 39.61 | -23.74 |
| Morning 06:00-11:59 | 290 | 0 | 92 | 196 | 31.72% | -857.71 | 0.75 | 28.34 | -17.68 |
| Afternoon 12:00-15:59 | 202 | 0 | 55 | 139 | 27.23% | -1061.10 | 0.54 | 22.53 | -16.55 |
| Night 20:00-05:59 | 487 | 0 | 172 | 303 | 35.32% | -1179.66 | 0.83 | 33.56 | -22.94 |

## Worst EA x Symbol x Time Clusters

| candidate | symbol | time_bucket | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| symbol_normalized_round_retest_v0 | XAUUSD | Morning 06:00-11:59 | 120 | 0 | 38 | 82 | 31.67% | -442.43 | 0.76 | 37.45 | -22.75 |
| symbol_normalized_round_retest_v0 | XAUUSD | Afternoon 12:00-15:59 | 64 | 0 | 18 | 46 | 28.12% | -442.11 | 0.62 | 39.52 | -25.08 |
| symbol_normalized_round_retest_v0 | XAUUSD | Evening 16:00-19:59 | 93 | 0 | 34 | 57 | 36.56% | -384.38 | 0.84 | 58.17 | -41.44 |
| symbol_normalized_round_retest_v0 | GBPUSD | Evening 16:00-19:59 | 25 | 0 | 3 | 20 | 12.00% | -278.51 | 0.24 | 28.70 | -18.23 |
| breakout_retest | GBPUSD | Night 20:00-05:59 | 42 | 0 | 14 | 23 | 33.33% | -275.38 | 0.51 | 20.08 | -24.19 |
| symbol_normalized_round_retest_v0 | GBPUSD | Morning 06:00-11:59 | 12 | 0 | 0 | 12 | 0.00% | -199.78 | 0.00 | n/a | -16.65 |
| breakout_retest | EURUSD | Night 20:00-05:59 | 47 | 0 | 15 | 31 | 31.91% | -166.51 | 0.60 | 16.45 | -13.33 |
| breakout_retest | GBPUSD | Evening 16:00-19:59 | 26 | 0 | 5 | 18 | 19.23% | -149.86 | 0.44 | 23.23 | -14.78 |
| swing_breakout_retest_v0 | XAUUSD | Morning 06:00-11:59 | 8 | 0 | 0 | 8 | 0.00% | -130.65 | 0.00 | n/a | -16.33 |
| breakout_retest | GBPUSD | Afternoon 12:00-15:59 | 13 | 0 | 1 | 11 | 7.69% | -128.21 | 0.04 | 5.51 | -12.16 |
| session_extreme_retest_v0 | EURUSD | Evening 16:00-19:59 | 20 | 0 | 4 | 11 | 20.00% | -124.18 | 0.15 | 5.52 | -13.30 |
| breakout_retest | EURUSD | Afternoon 12:00-15:59 | 21 | 0 | 6 | 15 | 28.57% | -120.27 | 0.31 | 9.19 | -11.69 |

## Promotion Rule

- A rule may be promoted only after it improves duplicate-hidden PF and PnL, preserves or improves win rate, keeps enough trade count, survives at least one fresh week, and receives owner/reviewer approval.
- This report is measurement-only and does not deploy a guard/router or change running EAs.
