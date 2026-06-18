# Phase 2 EA Weakness Shadow Report

Status: SHADOW_ONLY_NOT_ENFORCED

Measurement only. Does not change MT5 charts, EA inputs, orders, positions, presets, or runtime behavior.

Generated at UTC: `2026-06-17T22:23:02.808810Z`
History window: `2026-06-01 00:00:00` to `2026-06-18 02:23:02`
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
| Raw broker trades | 1942 | 1932 | 10 | 665 | 1217 | 34.42% | -2795.79 | 37.88 | -2757.91 | 0.91 | 40.29 | -24.31 |
| Duplicate-hidden decision view | 1192 | 1183 | 9 | 385 | 765 | 32.54% | -2954.02 | 22.31 | -2931.71 | 0.82 | 35.19 | -21.57 |
| Combined shadow would keep | 367 | 366 | 1 | 113 | 240 | 30.87% | -598.26 | 10.90 | -587.36 | 0.85 | 29.60 | -16.43 |
| Combined shadow would block | 825 | 817 | 8 | 272 | 525 | 33.29% | -2355.76 | 11.41 | -2344.35 | 0.81 | 37.51 | -23.92 |

## Shadow Scenarios

| Scenario | Baseline Closed | Kept Closed | Kept % | Delta PnL AED | Kept PF | Kept Win Rate | Promotion Status |
|---|---:|---:|---:|---:|---:|---:|---|
| Duplicate family mutex | 1932 | 1183 | 61.23% | -158.23 | 0.82 | 32.54% | REJECT_OR_KEEP_MEASURING |
| EA quarantine: session_extreme_retest_v0 | 1183 | 1045 | 88.33% | 222.83 | 0.82 | 33.01% | SHADOW_CANDIDATE_NEEDS_FORWARD_WEEK |
| EA quarantine: symbol_normalized_round_retest_v0 | 1183 | 589 | 49.79% | 2142.22 | 0.87 | 31.58% | REJECT_OR_KEEP_MEASURING |
| EA quarantine: round_number_retest_v0 | 1183 | 1143 | 96.62% | -16.86 | 0.81 | 32.20% | REJECT_OR_KEEP_MEASURING |
| Family quarantine: round-retest clone family | 1183 | 549 | 46.41% | 2125.36 | 0.86 | 30.78% | REJECT_OR_KEEP_MEASURING |
| Session filter: XAUUSD morning/afternoon | 1183 | 914 | 77.26% | 1036.68 | 0.85 | 32.82% | SHADOW_CANDIDATE_NEEDS_FORWARD_WEEK |
| Combined proposed shadow policy | 1183 | 366 | 30.94% | 2355.76 | 0.85 | 30.87% | FAIL_TRADE_COUNT |

## Block Reason Counts

| Reason | Count |
|---|---:|
| BLOCK_WEAK_EA_ROUND_RETEST_CLONE_FAMILY | 641 |
| BLOCK_WEAK_EA_SESSION_EXTREME_RETEST | 139 |
| BLOCK_XAUUSD_MORNING_AFTERNOON | 45 |

## Duplicate-Hidden By EA

| candidate | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| round_number_retest_v0 | 40 | 0 | 17 | 23 | 42.50% | 16.86 | 1.04 | 28.29 | -20.17 |
| p2weakness_br_v1 | 1 | 0 | 0 | 1 | 0.00% | -14.44 | 0.00 | n/a | -14.44 |
| symbol_normalized_round_retest_v0_repair_v1 | 4 | 0 | 1 | 3 | 25.00% | -17.35 | 0.78 | 62.71 | -26.69 |
| WR50_BreakoutEvening_v0 | 2 | 0 | 0 | 2 | 0.00% | -74.00 | 0.00 | n/a | -37.00 |
| swing_breakout_retest_v0 | 75 | 0 | 15 | 57 | 20.00% | -222.76 | 0.61 | 23.43 | -10.07 |
| session_extreme_retest_v0 | 138 | 1 | 40 | 87 | 28.99% | -222.83 | 0.82 | 26.05 | -14.54 |
| breakout_retest | 329 | 1 | 113 | 206 | 34.35% | -277.28 | 0.93 | 30.53 | -18.09 |
| symbol_normalized_round_retest_v0 | 594 | 7 | 199 | 386 | 33.50% | -2142.22 | 0.79 | 41.01 | -26.69 |

## Duplicate-Hidden By Symbol

| symbol | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| USDJPY | 21 | 0 | 4 | 16 | 19.05% | -24.94 | 0.45 | 5.14 | -2.84 |
| XAUUSD | 691 | 1 | 259 | 428 | 37.48% | -706.57 | 0.94 | 42.79 | -27.54 |
| EURUSD | 267 | 8 | 78 | 177 | 29.21% | -925.91 | 0.59 | 16.79 | -12.63 |
| GBPUSD | 204 | 0 | 44 | 144 | 21.57% | -1296.60 | 0.47 | 25.80 | -16.89 |

## Duplicate-Hidden By Time Bucket

| time_bucket | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Evening 16:00-19:59 | 289 | 0 | 105 | 173 | 36.33% | 5.05 | 1.00 | 40.12 | -24.32 |
| Morning 06:00-11:59 | 254 | 0 | 81 | 171 | 31.89% | -763.86 | 0.77 | 31.03 | -19.16 |
| Afternoon 12:00-15:59 | 191 | 0 | 49 | 134 | 25.65% | -1069.05 | 0.53 | 24.56 | -16.96 |
| Night 20:00-05:59 | 449 | 9 | 150 | 287 | 33.41% | -1126.16 | 0.83 | 37.45 | -23.50 |

## Worst EA x Symbol x Time Clusters

| candidate | symbol | time_bucket | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| symbol_normalized_round_retest_v0 | XAUUSD | Morning 06:00-11:59 | 120 | 0 | 38 | 82 | 31.67% | -442.43 | 0.76 | 37.45 | -22.75 |
| symbol_normalized_round_retest_v0 | XAUUSD | Afternoon 12:00-15:59 | 64 | 0 | 18 | 46 | 28.12% | -442.11 | 0.62 | 39.52 | -25.08 |
| symbol_normalized_round_retest_v0 | XAUUSD | Evening 16:00-19:59 | 93 | 0 | 34 | 57 | 36.56% | -384.38 | 0.84 | 58.17 | -41.44 |
| symbol_normalized_round_retest_v0 | GBPUSD | Evening 16:00-19:59 | 24 | 0 | 3 | 20 | 12.50% | -278.51 | 0.24 | 28.70 | -18.23 |
| breakout_retest | GBPUSD | Night 20:00-05:59 | 33 | 0 | 10 | 18 | 30.30% | -274.83 | 0.49 | 25.91 | -29.66 |
| symbol_normalized_round_retest_v0 | GBPUSD | Morning 06:00-11:59 | 11 | 0 | 0 | 11 | 0.00% | -196.22 | 0.00 | n/a | -17.84 |
| breakout_retest | EURUSD | Night 20:00-05:59 | 42 | 0 | 10 | 31 | 23.81% | -194.15 | 0.53 | 21.91 | -13.33 |
| symbol_normalized_round_retest_v0 | EURUSD | Night 20:00-05:59 | 37 | 7 | 11 | 26 | 29.73% | -157.61 | 0.65 | 26.45 | -17.25 |
| breakout_retest | GBPUSD | Evening 16:00-19:59 | 24 | 0 | 5 | 18 | 20.83% | -149.86 | 0.44 | 23.23 | -14.78 |
| breakout_retest | GBPUSD | Afternoon 12:00-15:59 | 11 | 0 | 0 | 10 | 0.00% | -129.94 | 0.00 | n/a | -12.99 |
| breakout_retest | EURUSD | Afternoon 12:00-15:59 | 20 | 0 | 5 | 15 | 25.00% | -125.81 | 0.28 | 9.92 | -11.69 |
| session_extreme_retest_v0 | EURUSD | Evening 16:00-19:59 | 20 | 0 | 4 | 11 | 20.00% | -124.18 | 0.15 | 5.52 | -13.30 |

## Promotion Rule

- A rule may be promoted only after it improves duplicate-hidden PF and PnL, preserves or improves win rate, keeps enough trade count, survives at least one fresh week, and receives owner/reviewer approval.
- This report is measurement-only and does not deploy a guard/router or change running EAs.
