# Phase 2 EA Weakness Shadow Report

Status: SHADOW_ONLY_NOT_ENFORCED

Measurement only. Does not change MT5 charts, EA inputs, orders, positions, presets, or runtime behavior.

Generated at UTC: `2026-06-08T12:48:54.500570Z`
History window: `2026-06-01 00:00:00` to `2026-06-08 16:48:54`
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
| Raw broker trades | 373 | 367 | 6 | 147 | 220 | 40.05% | 297.87 | 1.59 | 299.46 | 1.07 | 30.76 | -19.20 |
| Duplicate-hidden decision view | 217 | 214 | 3 | 83 | 131 | 38.79% | 32.96 | 0.50 | 33.46 | 1.01 | 28.38 | -17.73 |
| Combined shadow would keep | 78 | 76 | 2 | 35 | 41 | 46.05% | 481.11 | 2.71 | 483.82 | 2.21 | 25.08 | -9.68 |
| Combined shadow would block | 139 | 138 | 1 | 48 | 90 | 34.78% | -448.15 | -2.21 | -450.36 | 0.77 | 30.79 | -21.40 |

## Shadow Scenarios

| Scenario | Baseline Closed | Kept Closed | Kept % | Delta PnL AED | Kept PF | Kept Win Rate | Promotion Status |
|---|---:|---:|---:|---:|---:|---:|---|
| Duplicate family mutex | 367 | 214 | 58.31% | -264.91 | 1.01 | 38.79% | REJECT_OR_KEEP_MEASURING |
| EA quarantine: session_extreme_retest_v0 | 214 | 174 | 81.31% | 85.44 | 1.06 | 40.80% | SHADOW_CANDIDATE_NEEDS_FORWARD_WEEK |
| EA quarantine: symbol_normalized_round_retest_v0 | 214 | 134 | 62.62% | 315.51 | 1.35 | 38.81% | SHADOW_CANDIDATE_NEEDS_FORWARD_WEEK |
| Session filter: XAUUSD morning/afternoon | 214 | 151 | 70.56% | 309.53 | 1.26 | 42.38% | SHADOW_CANDIDATE_NEEDS_FORWARD_WEEK |
| Combined proposed shadow policy | 214 | 76 | 35.51% | 448.15 | 2.21 | 46.05% | SHADOW_CANDIDATE_NEEDS_FORWARD_WEEK |

## Block Reason Counts

| Reason | Count |
|---|---:|
| BLOCK_WEAK_EA_SYMBOL_NORMALIZED_ROUND | 81 |
| BLOCK_WEAK_EA_SESSION_EXTREME_RETEST | 40 |
| BLOCK_XAUUSD_MORNING_AFTERNOON | 18 |

## Duplicate-Hidden By EA

| candidate | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| breakout_retest | 81 | 1 | 37 | 44 | 45.68% | 461.23 | 1.82 | 27.59 | -12.72 |
| swing_breakout_retest_v0 | 11 | 1 | 3 | 8 | 27.27% | 46.68 | 2.93 | 23.62 | -3.02 |
| WR50_BreakoutEvening_v0 | 2 | 0 | 0 | 2 | 0.00% | -74.00 | 0.00 | n/a | -37.00 |
| session_extreme_retest_v0 | 40 | 0 | 12 | 28 | 30.00% | -85.44 | 0.75 | 21.21 | -12.14 |
| symbol_normalized_round_retest_v0 | 80 | 1 | 31 | 49 | 38.75% | -315.51 | 0.76 | 32.57 | -27.05 |

## Duplicate-Hidden By Symbol

| symbol | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| EURUSD | 45 | 1 | 22 | 23 | 48.89% | 33.27 | 1.38 | 5.49 | -3.80 |
| XAUUSD | 150 | 0 | 57 | 93 | 38.00% | 21.05 | 1.01 | 38.85 | -23.59 |
| USDJPY | 19 | 2 | 4 | 15 | 21.05% | -21.36 | 0.49 | 5.14 | -2.80 |

## Duplicate-Hidden By Time Bucket

| time_bucket | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Evening 16:00-19:59 | 38 | 0 | 22 | 16 | 57.89% | 395.81 | 2.35 | 31.33 | -18.34 |
| Night 20:00-05:59 | 85 | 0 | 31 | 54 | 36.47% | -60.96 | 0.94 | 29.82 | -18.25 |
| Afternoon 12:00-15:59 | 42 | 3 | 14 | 28 | 33.33% | -93.51 | 0.71 | 16.18 | -11.43 |
| Morning 06:00-11:59 | 49 | 0 | 16 | 33 | 32.65% | -208.38 | 0.71 | 32.23 | -21.94 |

## Worst EA x Symbol x Time Clusters

| candidate | symbol | time_bucket | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| symbol_normalized_round_retest_v0 | XAUUSD | Morning 06:00-11:59 | 30 | 0 | 10 | 20 | 33.33% | -195.31 | 0.64 | 34.93 | -27.23 |
| session_extreme_retest_v0 | XAUUSD | Night 20:00-05:59 | 10 | 0 | 1 | 9 | 10.00% | -112.94 | 0.31 | 50.19 | -18.13 |
| symbol_normalized_round_retest_v0 | XAUUSD | Afternoon 12:00-15:59 | 4 | 0 | 0 | 4 | 0.00% | -88.40 | 0.00 | n/a | -22.10 |
| WR50_BreakoutEvening_v0 | XAUUSD | Night 20:00-05:59 | 2 | 0 | 0 | 2 | 0.00% | -74.00 | 0.00 | n/a | -37.00 |
| breakout_retest | XAUUSD | Afternoon 12:00-15:59 | 7 | 0 | 2 | 5 | 28.57% | -33.45 | 0.66 | 31.98 | -19.48 |
| symbol_normalized_round_retest_v0 | XAUUSD | Night 20:00-05:59 | 33 | 0 | 14 | 19 | 42.42% | -27.51 | 0.94 | 33.27 | -25.97 |
| symbol_normalized_round_retest_v0 | XAUUSD | Evening 16:00-19:59 | 8 | 0 | 3 | 5 | 37.50% | -22.24 | 0.89 | 57.69 | -39.06 |
| breakout_retest | XAUUSD | Morning 06:00-11:59 | 11 | 0 | 3 | 8 | 27.27% | -13.75 | 0.92 | 49.94 | -20.45 |
| swing_breakout_retest_v0 | USDJPY | Night 20:00-05:59 | 2 | 0 | 0 | 2 | 0.00% | -10.38 | 0.00 | n/a | -5.19 |
| session_extreme_retest_v0 | USDJPY | Evening 16:00-19:59 | 3 | 0 | 0 | 3 | 0.00% | -10.35 | 0.00 | n/a | -3.45 |
| breakout_retest | EURUSD | Afternoon 12:00-15:59 | 10 | 0 | 3 | 7 | 30.00% | -10.25 | 0.62 | 5.52 | -3.83 |
| session_extreme_retest_v0 | USDJPY | Night 20:00-05:59 | 2 | 0 | 0 | 2 | 0.00% | -5.76 | 0.00 | n/a | -2.88 |

## Promotion Rule

- A rule may be promoted only after it improves duplicate-hidden PF and PnL, preserves or improves win rate, keeps enough trade count, survives at least one fresh week, and receives owner/reviewer approval.
- This report is measurement-only and does not deploy a guard/router or change running EAs.
