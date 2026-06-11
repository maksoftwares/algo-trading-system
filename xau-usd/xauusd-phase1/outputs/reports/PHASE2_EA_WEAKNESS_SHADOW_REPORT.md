# Phase 2 EA Weakness Shadow Report

Status: SHADOW_ONLY_NOT_ENFORCED

Measurement only. Does not change MT5 charts, EA inputs, orders, positions, presets, or runtime behavior.

Generated at UTC: `2026-06-09T20:49:50.186483Z`
History window: `2026-06-01 00:00:00` to `2026-06-10 00:49:50`
Account: `1025742` / `Capital.ComMena-Demo` / `AED`

## Policy Under Measurement

- Use duplicate-hidden actual trades as the main decision view.
- Measure one-event-per-family duplicate mutex.
- Keep duplicate priority: breakout_retest, swing_breakout_retest_v0, symbol_normalized_round_retest_v0, then provisional/experimental EAs.
- Measure separate EA quarantine for session_extreme_retest_v0 and symbol_normalized_round_retest_v0.
- Measure XAUUSD morning/afternoon session block.
- Promote only after owner/reviewer approval and at least one fresh forward week.

## Main Decision Views

| View | Trades | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | Floating AED | Total AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Raw broker trades | 565 | 545 | 20 | 209 | 334 | 38.35% | 720.84 | -81.46 | 639.38 | 1.10 | 36.72 | -20.82 |
| Duplicate-hidden decision view | 318 | 305 | 13 | 110 | 194 | 36.07% | -329.65 | -18.77 | -348.42 | 0.91 | 31.35 | -19.47 |
| Combined shadow would keep | 102 | 99 | 3 | 45 | 54 | 45.45% | 584.86 | -16.68 | 568.18 | 1.89 | 27.57 | -12.14 |
| Combined shadow would block | 216 | 206 | 10 | 65 | 140 | 31.55% | -914.51 | -2.09 | -916.60 | 0.71 | 33.97 | -22.30 |

## Shadow Scenarios

| Scenario | Baseline Closed | Kept Closed | Kept % | Delta PnL AED | Kept PF | Kept Win Rate | Promotion Status |
|---|---:|---:|---:|---:|---:|---:|---|
| Duplicate family mutex | 545 | 305 | 55.96% | -1050.49 | 0.91 | 36.07% | REJECT_OR_KEEP_MEASURING |
| EA quarantine: session_extreme_retest_v0 | 305 | 250 | 81.97% | 208.52 | 0.96 | 38.00% | SHADOW_CANDIDATE_NEEDS_FORWARD_WEEK |
| EA quarantine: symbol_normalized_round_retest_v0 | 305 | 174 | 57.05% | 630.46 | 1.20 | 37.36% | SHADOW_CANDIDATE_NEEDS_FORWARD_WEEK |
| Session filter: XAUUSD morning/afternoon | 305 | 231 | 75.74% | 389.79 | 1.02 | 38.10% | SHADOW_CANDIDATE_NEEDS_FORWARD_WEEK |
| Combined proposed shadow policy | 305 | 99 | 32.46% | 914.51 | 1.89 | 45.45% | FAIL_TRADE_COUNT |

## Block Reason Counts

| Reason | Count |
|---|---:|
| BLOCK_WEAK_EA_SYMBOL_NORMALIZED_ROUND | 140 |
| BLOCK_WEAK_EA_SESSION_EXTREME_RETEST | 56 |
| BLOCK_XAUUSD_MORNING_AFTERNOON | 20 |

## Duplicate-Hidden By EA

| candidate | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| breakout_retest | 103 | 3 | 46 | 57 | 44.66% | 567.81 | 1.70 | 29.95 | -14.21 |
| swing_breakout_retest_v0 | 12 | 0 | 4 | 8 | 33.33% | 52.19 | 3.16 | 19.09 | -3.02 |
| p2weakness_br_v1 | 1 | 0 | 0 | 1 | 0.00% | -14.44 | 0.00 | n/a | -14.44 |
| symbol_normalized_round_retest_v0_repair_v1 | 1 | 0 | 0 | 1 | 0.00% | -22.23 | 0.00 | n/a | -22.23 |
| WR50_BreakoutEvening_v0 | 2 | 0 | 0 | 2 | 0.00% | -74.00 | 0.00 | n/a | -37.00 |
| session_extreme_retest_v0 | 55 | 1 | 15 | 40 | 27.27% | -208.52 | 0.64 | 24.73 | -14.49 |
| symbol_normalized_round_retest_v0 | 131 | 9 | 45 | 85 | 34.35% | -630.46 | 0.72 | 36.07 | -26.51 |

## Duplicate-Hidden By Symbol

| symbol | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| USDJPY | 21 | 0 | 4 | 16 | 19.05% | -24.94 | 0.45 | 5.14 | -2.84 |
| GBPUSD | 15 | 2 | 5 | 10 | 33.33% | -62.35 | 0.61 | 19.54 | -16.01 |
| EURUSD | 61 | 7 | 26 | 35 | 42.62% | -102.82 | 0.67 | 8.03 | -8.91 |
| XAUUSD | 208 | 4 | 75 | 133 | 36.06% | -139.54 | 0.96 | 41.62 | -24.52 |

## Duplicate-Hidden By Time Bucket

| time_bucket | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Evening 16:00-19:59 | 76 | 0 | 35 | 41 | 46.05% | 426.35 | 1.47 | 37.87 | -21.93 |
| Afternoon 12:00-15:59 | 51 | 0 | 17 | 33 | 33.33% | -134.33 | 0.68 | 16.89 | -12.77 |
| Morning 06:00-11:59 | 56 | 0 | 19 | 37 | 33.93% | -190.81 | 0.76 | 31.73 | -21.45 |
| Night 20:00-05:59 | 122 | 13 | 39 | 83 | 31.97% | -430.86 | 0.74 | 31.62 | -20.05 |

## Worst EA x Symbol x Time Clusters

| candidate | symbol | time_bucket | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| symbol_normalized_round_retest_v0 | XAUUSD | Night 20:00-05:59 | 51 | 3 | 18 | 33 | 35.29% | -208.78 | 0.75 | 35.30 | -25.58 |
| symbol_normalized_round_retest_v0 | XAUUSD | Afternoon 12:00-15:59 | 7 | 0 | 0 | 7 | 0.00% | -172.34 | 0.00 | n/a | -24.62 |
| symbol_normalized_round_retest_v0 | XAUUSD | Morning 06:00-11:59 | 36 | 0 | 13 | 23 | 36.11% | -163.30 | 0.73 | 33.58 | -26.08 |
| session_extreme_retest_v0 | XAUUSD | Night 20:00-05:59 | 12 | 0 | 2 | 10 | 16.67% | -96.39 | 0.48 | 44.16 | -18.47 |
| session_extreme_retest_v0 | EURUSD | Night 20:00-05:59 | 9 | 1 | 3 | 6 | 33.33% | -79.76 | 0.17 | 5.50 | -16.04 |
| WR50_BreakoutEvening_v0 | XAUUSD | Night 20:00-05:59 | 2 | 0 | 0 | 2 | 0.00% | -74.00 | 0.00 | n/a | -37.00 |
| session_extreme_retest_v0 | EURUSD | Evening 16:00-19:59 | 4 | 0 | 0 | 4 | 0.00% | -62.64 | 0.00 | n/a | -15.66 |
| breakout_retest | XAUUSD | Afternoon 12:00-15:59 | 8 | 0 | 2 | 6 | 25.00% | -47.34 | 0.57 | 31.98 | -18.55 |
| breakout_retest | EURUSD | Night 20:00-05:59 | 13 | 0 | 4 | 9 | 30.77% | -41.61 | 0.35 | 5.50 | -7.07 |
| symbol_normalized_round_retest_v0 | GBPUSD | Evening 16:00-19:59 | 8 | 0 | 2 | 6 | 25.00% | -39.09 | 0.60 | 29.46 | -16.34 |
| symbol_normalized_round_retest_v0 | EURUSD | Night 20:00-05:59 | 2 | 6 | 0 | 2 | 0.00% | -36.56 | 0.00 | n/a | -18.28 |
| symbol_normalized_round_retest_v0 | XAUUSD | Evening 16:00-19:59 | 21 | 0 | 8 | 13 | 38.10% | -28.34 | 0.94 | 58.84 | -38.39 |

## Promotion Rule

- A rule may be promoted only after it improves duplicate-hidden PF and PnL, preserves or improves win rate, keeps enough trade count, survives at least one fresh week, and receives owner/reviewer approval.
- This report is measurement-only and does not deploy a guard/router or change running EAs.
