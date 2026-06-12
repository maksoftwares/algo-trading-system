# Phase 2 EA Weakness Shadow Report

Status: SHADOW_ONLY_NOT_ENFORCED

Measurement only. Does not change MT5 charts, EA inputs, orders, positions, presets, or runtime behavior.

Generated at UTC: `2026-06-12T23:17:39.641095Z`
History window: `2026-06-01 00:00:00` to `2026-06-13 03:17:39`
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
| Raw broker trades | 1510 | 1502 | 8 | 536 | 933 | 35.69% | -1963.87 | 44.78 | -1919.09 | 0.92 | 43.41 | -27.04 |
| Duplicate-hidden decision view | 796 | 792 | 4 | 272 | 504 | 34.34% | -2156.58 | 24.04 | -2132.54 | 0.83 | 38.79 | -25.21 |
| Combined shadow would keep | 219 | 216 | 3 | 76 | 136 | 35.19% | -106.94 | -2.39 | -109.33 | 0.96 | 31.35 | -18.30 |
| Combined shadow would block | 577 | 576 | 1 | 196 | 368 | 34.03% | -2049.64 | 26.43 | -2023.21 | 0.80 | 41.67 | -27.76 |

## Shadow Scenarios

| Scenario | Baseline Closed | Kept Closed | Kept % | Delta PnL AED | Kept PF | Kept Win Rate | Promotion Status |
|---|---:|---:|---:|---:|---:|---:|---|
| Duplicate family mutex | 1502 | 792 | 52.73% | -192.71 | 0.83 | 34.34% | REJECT_OR_KEEP_MEASURING |
| EA quarantine: session_extreme_retest_v0 | 792 | 698 | 88.13% | 299.94 | 0.84 | 35.24% | SHADOW_CANDIDATE_NEEDS_FORWARD_WEEK |
| EA quarantine: symbol_normalized_round_retest_v0 | 792 | 343 | 43.31% | 1749.10 | 0.90 | 32.94% | REJECT_OR_KEEP_MEASURING |
| EA quarantine: round_number_retest_v0 | 792 | 789 | 99.62% | -11.76 | 0.83 | 34.35% | REJECT_OR_KEEP_MEASURING |
| Family quarantine: round-retest clone family | 792 | 340 | 42.93% | 1737.34 | 0.89 | 32.94% | REJECT_OR_KEEP_MEASURING |
| Session filter: XAUUSD morning/afternoon | 792 | 617 | 77.90% | 486.16 | 0.83 | 34.20% | REJECT_OR_KEEP_MEASURING |
| Combined proposed shadow policy | 792 | 216 | 27.27% | 2049.64 | 0.96 | 35.19% | FAIL_TRADE_COUNT |

## Block Reason Counts

| Reason | Count |
|---|---:|
| BLOCK_WEAK_EA_ROUND_RETEST_CLONE_FAMILY | 453 |
| BLOCK_WEAK_EA_SESSION_EXTREME_RETEST | 94 |
| BLOCK_XAUUSD_MORNING_AFTERNOON | 30 |

## Duplicate-Hidden By EA

| candidate | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| swing_breakout_retest_v0 | 15 | 0 | 5 | 10 | 33.33% | 42.98 | 1.70 | 20.85 | -6.13 |
| round_number_retest_v0 | 3 | 0 | 1 | 2 | 33.33% | 11.76 | 1.38 | 42.59 | -15.41 |
| p2weakness_br_v1 | 1 | 0 | 0 | 1 | 0.00% | -14.44 | 0.00 | n/a | -14.44 |
| symbol_normalized_round_retest_v0_repair_v1 | 1 | 0 | 0 | 1 | 0.00% | -22.23 | 0.00 | n/a | -22.23 |
| breakout_retest | 227 | 3 | 81 | 142 | 35.68% | -51.61 | 0.98 | 32.88 | -19.12 |
| WR50_BreakoutEvening_v0 | 2 | 0 | 0 | 2 | 0.00% | -74.00 | 0.00 | n/a | -37.00 |
| session_extreme_retest_v0 | 94 | 0 | 26 | 62 | 27.66% | -299.94 | 0.70 | 27.52 | -16.38 |
| symbol_normalized_round_retest_v0 | 449 | 1 | 159 | 284 | 35.41% | -1749.10 | 0.80 | 44.18 | -30.89 |

## Duplicate-Hidden By Symbol

| symbol | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| USDJPY | 21 | 0 | 4 | 16 | 19.05% | -24.94 | 0.45 | 5.14 | -2.84 |
| EURUSD | 154 | 1 | 50 | 98 | 32.47% | -618.32 | 0.59 | 17.62 | -15.30 |
| XAUUSD | 500 | 1 | 188 | 308 | 37.60% | -630.79 | 0.93 | 46.90 | -30.67 |
| GBPUSD | 117 | 2 | 30 | 82 | 25.64% | -882.53 | 0.49 | 27.72 | -20.90 |

## Duplicate-Hidden By Time Bucket

| time_bucket | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Evening 16:00-19:59 | 194 | 0 | 70 | 113 | 36.08% | -204.01 | 0.94 | 45.50 | -29.99 |
| Morning 06:00-11:59 | 159 | 0 | 53 | 106 | 33.33% | -487.84 | 0.79 | 34.82 | -22.01 |
| Night 20:00-05:59 | 316 | 4 | 115 | 197 | 36.39% | -708.04 | 0.87 | 39.53 | -26.67 |
| Afternoon 12:00-15:59 | 123 | 0 | 34 | 88 | 27.64% | -756.69 | 0.56 | 28.64 | -19.66 |

## Worst EA x Symbol x Time Clusters

| candidate | symbol | time_bucket | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| symbol_normalized_round_retest_v0 | XAUUSD | Evening 16:00-19:59 | 80 | 0 | 27 | 51 | 33.75% | -518.49 | 0.77 | 63.08 | -43.56 |
| symbol_normalized_round_retest_v0 | XAUUSD | Night 20:00-05:59 | 158 | 1 | 62 | 95 | 39.24% | -311.47 | 0.90 | 46.91 | -33.89 |
| symbol_normalized_round_retest_v0 | GBPUSD | Evening 16:00-19:59 | 22 | 0 | 3 | 18 | 13.64% | -270.39 | 0.24 | 28.70 | -19.80 |
| symbol_normalized_round_retest_v0 | XAUUSD | Afternoon 12:00-15:59 | 43 | 0 | 14 | 29 | 32.56% | -263.14 | 0.70 | 42.90 | -29.78 |
| symbol_normalized_round_retest_v0 | XAUUSD | Morning 06:00-11:59 | 86 | 0 | 32 | 54 | 37.21% | -190.06 | 0.87 | 38.47 | -26.32 |
| breakout_retest | GBPUSD | Night 20:00-05:59 | 24 | 2 | 8 | 14 | 33.33% | -186.32 | 0.52 | 25.53 | -27.90 |
| breakout_retest | GBPUSD | Morning 06:00-11:59 | 19 | 0 | 4 | 15 | 21.05% | -165.02 | 0.40 | 27.95 | -18.46 |
| symbol_normalized_round_retest_v0 | GBPUSD | Morning 06:00-11:59 | 7 | 0 | 0 | 7 | 0.00% | -133.18 | 0.00 | n/a | -19.03 |
| breakout_retest | EURUSD | Afternoon 12:00-15:59 | 19 | 0 | 4 | 15 | 21.05% | -131.32 | 0.25 | 11.03 | -11.69 |
| breakout_retest | EURUSD | Morning 06:00-11:59 | 12 | 0 | 2 | 10 | 16.67% | -129.58 | 0.08 | 5.51 | -14.06 |
| session_extreme_retest_v0 | EURUSD | Evening 16:00-19:59 | 12 | 0 | 0 | 7 | 0.00% | -116.83 | 0.00 | n/a | -16.69 |
| breakout_retest | GBPUSD | Afternoon 12:00-15:59 | 6 | 0 | 0 | 6 | 0.00% | -115.18 | 0.00 | n/a | -19.20 |

## Promotion Rule

- A rule may be promoted only after it improves duplicate-hidden PF and PnL, preserves or improves win rate, keeps enough trade count, survives at least one fresh week, and receives owner/reviewer approval.
- This report is measurement-only and does not deploy a guard/router or change running EAs.
