# Phase 2 EA Weakness Shadow Report

Status: SHADOW_ONLY_NOT_ENFORCED

Measurement only. Does not change MT5 charts, EA inputs, orders, positions, presets, or runtime behavior.

Generated at UTC: `2026-06-08T14:47:47.205468Z`
History window: `2026-06-01 00:00:00` to `2026-06-08 18:47:47`
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
| Raw broker trades | 384 | 377 | 7 | 150 | 227 | 39.79% | 288.73 | 22.76 | 311.49 | 1.07 | 30.92 | -19.16 |
| Duplicate-hidden decision view | 225 | 220 | 5 | 85 | 135 | 38.64% | 9.04 | 16.32 | 25.36 | 1.00 | 28.43 | -17.84 |
| Combined shadow would keep | 79 | 78 | 1 | 36 | 42 | 46.15% | 483.04 | 4.08 | 487.12 | 2.21 | 24.54 | -9.53 |
| Combined shadow would block | 146 | 142 | 4 | 49 | 93 | 34.51% | -474.00 | 12.24 | -461.76 | 0.76 | 31.30 | -21.59 |

## Shadow Scenarios

| Scenario | Baseline Closed | Kept Closed | Kept % | Delta PnL AED | Kept PF | Kept Win Rate | Promotion Status |
|---|---:|---:|---:|---:|---:|---:|---|
| Duplicate family mutex | 377 | 220 | 58.36% | -279.69 | 1.00 | 38.64% | REJECT_OR_KEEP_MEASURING |
| EA quarantine: session_extreme_retest_v0 | 220 | 178 | 80.91% | 133.23 | 1.07 | 41.01% | SHADOW_CANDIDATE_NEEDS_FORWARD_WEEK |
| EA quarantine: symbol_normalized_round_retest_v0 | 220 | 138 | 62.73% | 293.57 | 1.29 | 38.41% | REJECT_OR_KEEP_MEASURING |
| Session filter: XAUUSD morning/afternoon | 220 | 157 | 71.36% | 309.53 | 1.22 | 42.04% | SHADOW_CANDIDATE_NEEDS_FORWARD_WEEK |
| Combined proposed shadow policy | 220 | 78 | 35.45% | 474.00 | 2.21 | 46.15% | SHADOW_CANDIDATE_NEEDS_FORWARD_WEEK |

## Block Reason Counts

| Reason | Count |
|---|---:|
| BLOCK_WEAK_EA_SYMBOL_NORMALIZED_ROUND | 84 |
| BLOCK_WEAK_EA_SESSION_EXTREME_RETEST | 44 |
| BLOCK_XAUUSD_MORNING_AFTERNOON | 18 |

## Duplicate-Hidden By EA

| candidate | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| breakout_retest | 82 | 1 | 37 | 45 | 45.12% | 457.65 | 1.81 | 27.59 | -12.51 |
| swing_breakout_retest_v0 | 12 | 0 | 4 | 8 | 33.33% | 52.19 | 3.16 | 19.09 | -3.02 |
| WR50_BreakoutEvening_v0 | 2 | 0 | 0 | 2 | 0.00% | -74.00 | 0.00 | n/a | -37.00 |
| session_extreme_retest_v0 | 42 | 2 | 12 | 30 | 28.57% | -133.23 | 0.66 | 21.21 | -12.92 |
| symbol_normalized_round_retest_v0 | 82 | 2 | 32 | 50 | 39.02% | -293.57 | 0.78 | 33.29 | -27.18 |

## Duplicate-Hidden By Symbol

| symbol | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| EURUSD | 46 | 1 | 23 | 23 | 50.00% | 38.78 | 1.44 | 5.49 | -3.80 |
| GBPUSD | 0 | 2 | 0 | 0 | n/a% | 0.00 | n/a | n/a | n/a |
| XAUUSD | 154 | 1 | 58 | 96 | 37.66% | -4.80 | 1.00 | 39.14 | -23.70 |
| USDJPY | 20 | 1 | 4 | 16 | 20.00% | -24.94 | 0.45 | 5.14 | -2.84 |

## Duplicate-Hidden By Time Bucket

| time_bucket | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Evening 16:00-19:59 | 42 | 4 | 23 | 19 | 54.76% | 369.96 | 1.99 | 32.38 | -19.72 |
| Night 20:00-05:59 | 85 | 0 | 31 | 54 | 36.47% | -60.96 | 0.94 | 29.82 | -18.25 |
| Afternoon 12:00-15:59 | 44 | 1 | 15 | 29 | 34.09% | -91.58 | 0.72 | 15.47 | -11.16 |
| Morning 06:00-11:59 | 49 | 0 | 16 | 33 | 32.65% | -208.38 | 0.71 | 32.23 | -21.94 |

## Worst EA x Symbol x Time Clusters

| candidate | symbol | time_bucket | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| symbol_normalized_round_retest_v0 | XAUUSD | Morning 06:00-11:59 | 30 | 0 | 10 | 20 | 33.33% | -195.31 | 0.64 | 34.93 | -27.23 |
| session_extreme_retest_v0 | XAUUSD | Night 20:00-05:59 | 10 | 0 | 1 | 9 | 10.00% | -112.94 | 0.31 | 50.19 | -18.13 |
| symbol_normalized_round_retest_v0 | XAUUSD | Afternoon 12:00-15:59 | 4 | 0 | 0 | 4 | 0.00% | -88.40 | 0.00 | n/a | -22.10 |
| WR50_BreakoutEvening_v0 | XAUUSD | Night 20:00-05:59 | 2 | 0 | 0 | 2 | 0.00% | -74.00 | 0.00 | n/a | -37.00 |
| session_extreme_retest_v0 | XAUUSD | Evening 16:00-19:59 | 6 | 1 | 2 | 4 | 33.33% | -33.84 | 0.66 | 32.33 | -24.62 |
| breakout_retest | XAUUSD | Afternoon 12:00-15:59 | 7 | 0 | 2 | 5 | 28.57% | -33.45 | 0.66 | 31.98 | -19.48 |
| symbol_normalized_round_retest_v0 | XAUUSD | Night 20:00-05:59 | 33 | 0 | 14 | 19 | 42.42% | -27.51 | 0.94 | 33.27 | -25.97 |
| breakout_retest | XAUUSD | Morning 06:00-11:59 | 11 | 0 | 3 | 8 | 27.27% | -13.75 | 0.92 | 49.94 | -20.45 |
| swing_breakout_retest_v0 | USDJPY | Night 20:00-05:59 | 2 | 0 | 0 | 2 | 0.00% | -10.38 | 0.00 | n/a | -5.19 |
| session_extreme_retest_v0 | USDJPY | Evening 16:00-19:59 | 3 | 0 | 0 | 3 | 0.00% | -10.35 | 0.00 | n/a | -3.45 |
| breakout_retest | EURUSD | Afternoon 12:00-15:59 | 10 | 0 | 3 | 7 | 30.00% | -10.25 | 0.62 | 5.52 | -3.83 |
| session_extreme_retest_v0 | USDJPY | Night 20:00-05:59 | 2 | 0 | 0 | 2 | 0.00% | -5.76 | 0.00 | n/a | -2.88 |

## Promotion Rule

- A rule may be promoted only after it improves duplicate-hidden PF and PnL, preserves or improves win rate, keeps enough trade count, survives at least one fresh week, and receives owner/reviewer approval.
- This report is measurement-only and does not deploy a guard/router or change running EAs.
