# Phase 2 EA Weakness Shadow Report

Status: SHADOW_ONLY_NOT_ENFORCED

Measurement only. Does not change MT5 charts, EA inputs, orders, positions, presets, or runtime behavior.

Generated at UTC: `2026-06-08T08:48:22.832079Z`
History window: `2026-06-01 00:00:00` to `2026-06-08 12:48:22`
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
| Raw broker trades | 361 | 355 | 6 | 142 | 213 | 40.00% | 153.26 | 87.75 | 241.01 | 1.04 | 30.38 | -19.53 |
| Duplicate-hidden decision view | 209 | 205 | 4 | 79 | 126 | 38.54% | -40.61 | 42.34 | 1.73 | 0.98 | 28.41 | -18.13 |
| Combined shadow would keep | 73 | 71 | 2 | 33 | 38 | 46.48% | 484.05 | -3.07 | 480.98 | 2.26 | 26.26 | -10.07 |
| Combined shadow would block | 136 | 134 | 2 | 46 | 88 | 34.33% | -524.66 | 45.41 | -479.25 | 0.72 | 29.94 | -21.61 |

## Shadow Scenarios

| Scenario | Baseline Closed | Kept Closed | Kept % | Delta PnL AED | Kept PF | Kept Win Rate | Promotion Status |
|---|---:|---:|---:|---:|---:|---:|---|
| Duplicate family mutex | 355 | 205 | 57.75% | -193.87 | 0.98 | 38.54% | REJECT_OR_KEEP_MEASURING |
| EA quarantine: session_extreme_retest_v0 | 205 | 166 | 80.98% | 81.73 | 1.02 | 40.36% | SHADOW_CANDIDATE_NEEDS_FORWARD_WEEK |
| EA quarantine: symbol_normalized_round_retest_v0 | 205 | 127 | 61.95% | 300.41 | 1.27 | 38.58% | SHADOW_CANDIDATE_NEEDS_FORWARD_WEEK |
| Session filter: XAUUSD morning/afternoon | 205 | 144 | 70.24% | 384.28 | 1.26 | 42.36% | SHADOW_CANDIDATE_NEEDS_FORWARD_WEEK |
| Combined proposed shadow policy | 205 | 71 | 34.63% | 524.66 | 2.26 | 46.48% | FAIL_TRADE_COUNT |

## Block Reason Counts

| Reason | Count |
|---|---:|
| BLOCK_WEAK_EA_SYMBOL_NORMALIZED_ROUND | 78 |
| BLOCK_WEAK_EA_SESSION_EXTREME_RETEST | 40 |
| BLOCK_XAUUSD_MORNING_AFTERNOON | 18 |

## Duplicate-Hidden By EA

| candidate | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| breakout_retest | 77 | 2 | 34 | 43 | 44.16% | 358.83 | 1.65 | 26.89 | -12.92 |
| swing_breakout_retest_v0 | 9 | 1 | 3 | 6 | 33.33% | 56.70 | 5.00 | 23.62 | -2.36 |
| WR50_BreakoutEvening_v0 | 2 | 0 | 0 | 2 | 0.00% | -74.00 | 0.00 | n/a | -37.00 |
| session_extreme_retest_v0 | 39 | 1 | 12 | 27 | 30.77% | -81.73 | 0.76 | 21.21 | -12.45 |
| symbol_normalized_round_retest_v0 | 78 | 0 | 30 | 48 | 38.46% | -300.41 | 0.77 | 33.48 | -27.18 |

## Duplicate-Hidden By Symbol

| symbol | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| EURUSD | 40 | 1 | 19 | 21 | 47.50% | 24.47 | 1.31 | 5.49 | -3.80 |
| USDJPY | 17 | 2 | 4 | 13 | 23.53% | -11.38 | 0.64 | 5.14 | -2.46 |
| XAUUSD | 148 | 1 | 56 | 92 | 37.84% | -53.70 | 0.98 | 37.84 | -23.62 |

## Duplicate-Hidden By Time Bucket

| time_bucket | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Evening 16:00-19:59 | 37 | 1 | 22 | 15 | 59.46% | 399.52 | 2.38 | 31.33 | -19.31 |
| Night 20:00-05:59 | 84 | 1 | 31 | 53 | 36.90% | -54.69 | 0.94 | 29.82 | -18.48 |
| Afternoon 12:00-15:59 | 36 | 1 | 11 | 25 | 30.56% | -81.74 | 0.72 | 19.09 | -11.67 |
| Morning 06:00-11:59 | 48 | 1 | 15 | 33 | 31.25% | -303.70 | 0.58 | 28.02 | -21.94 |

## Worst EA x Symbol x Time Clusters

| candidate | symbol | time_bucket | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| symbol_normalized_round_retest_v0 | XAUUSD | Morning 06:00-11:59 | 30 | 0 | 10 | 20 | 33.33% | -195.31 | 0.64 | 34.93 | -27.23 |
| session_extreme_retest_v0 | XAUUSD | Night 20:00-05:59 | 10 | 0 | 1 | 9 | 10.00% | -112.94 | 0.31 | 50.19 | -18.13 |
| breakout_retest | XAUUSD | Morning 06:00-11:59 | 10 | 1 | 2 | 8 | 20.00% | -109.07 | 0.33 | 27.26 | -20.45 |
| WR50_BreakoutEvening_v0 | XAUUSD | Night 20:00-05:59 | 2 | 0 | 0 | 2 | 0.00% | -74.00 | 0.00 | n/a | -37.00 |
| symbol_normalized_round_retest_v0 | XAUUSD | Afternoon 12:00-15:59 | 3 | 0 | 0 | 3 | 0.00% | -67.83 | 0.00 | n/a | -22.61 |
| breakout_retest | XAUUSD | Afternoon 12:00-15:59 | 7 | 0 | 2 | 5 | 28.57% | -33.45 | 0.66 | 31.98 | -19.48 |
| symbol_normalized_round_retest_v0 | XAUUSD | Night 20:00-05:59 | 33 | 0 | 14 | 19 | 42.42% | -27.51 | 0.94 | 33.27 | -25.97 |
| symbol_normalized_round_retest_v0 | XAUUSD | Evening 16:00-19:59 | 8 | 0 | 3 | 5 | 37.50% | -22.24 | 0.89 | 57.69 | -39.06 |
| breakout_retest | EURUSD | Afternoon 12:00-15:59 | 7 | 1 | 1 | 6 | 14.29% | -17.33 | 0.24 | 5.51 | -3.81 |
| session_extreme_retest_v0 | USDJPY | Evening 16:00-19:59 | 2 | 1 | 0 | 2 | 0.00% | -6.64 | 0.00 | n/a | -3.32 |
| session_extreme_retest_v0 | USDJPY | Night 20:00-05:59 | 2 | 0 | 0 | 2 | 0.00% | -5.76 | 0.00 | n/a | -2.88 |
| breakout_retest | EURUSD | Night 20:00-05:59 | 11 | 0 | 4 | 7 | 36.36% | -5.37 | 0.80 | 5.50 | -3.91 |

## Promotion Rule

- A rule may be promoted only after it improves duplicate-hidden PF and PnL, preserves or improves win rate, keeps enough trade count, survives at least one fresh week, and receives owner/reviewer approval.
- This report is measurement-only and does not deploy a guard/router or change running EAs.
