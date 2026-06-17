# Phase 2 EA Weakness Shadow Report

Status: SHADOW_ONLY_NOT_ENFORCED

Measurement only. Does not change MT5 charts, EA inputs, orders, positions, presets, or runtime behavior.

Generated at UTC: `2026-06-16T06:40:05.729423Z`
History window: `2026-06-01 00:00:00` to `2026-06-16 10:40:05`
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
| Raw broker trades | 1696 | 1692 | 4 | 599 | 1044 | 35.40% | -2207.89 | -72.34 | -2280.23 | 0.92 | 42.23 | -26.34 |
| Duplicate-hidden decision view | 970 | 966 | 4 | 325 | 609 | 33.64% | -2497.85 | -72.34 | -2570.19 | 0.83 | 37.72 | -24.23 |
| Combined shadow would keep | 290 | 288 | 2 | 101 | 174 | 35.07% | -94.01 | -24.98 | -118.99 | 0.97 | 31.25 | -18.68 |
| Combined shadow would block | 680 | 678 | 2 | 224 | 435 | 33.04% | -2403.84 | -47.36 | -2451.20 | 0.79 | 40.64 | -26.45 |

## Shadow Scenarios

| Scenario | Baseline Closed | Kept Closed | Kept % | Delta PnL AED | Kept PF | Kept Win Rate | Promotion Status |
|---|---:|---:|---:|---:|---:|---:|---|
| Duplicate family mutex | 1692 | 966 | 57.09% | -289.96 | 0.83 | 33.64% | REJECT_OR_KEEP_MEASURING |
| EA quarantine: session_extreme_retest_v0 | 966 | 858 | 88.82% | 373.23 | 0.84 | 34.62% | SHADOW_CANDIDATE_NEEDS_FORWARD_WEEK |
| EA quarantine: symbol_normalized_round_retest_v0 | 966 | 451 | 46.69% | 1982.07 | 0.90 | 33.04% | REJECT_OR_KEEP_MEASURING |
| EA quarantine: round_number_retest_v0 | 966 | 945 | 97.83% | 66.12 | 0.83 | 33.54% | REJECT_OR_KEEP_MEASURING |
| Family quarantine: round-retest clone family | 966 | 430 | 44.51% | 2048.19 | 0.91 | 32.79% | REJECT_OR_KEEP_MEASURING |
| Session filter: XAUUSD morning/afternoon | 966 | 748 | 77.43% | 733.99 | 0.84 | 33.82% | SHADOW_CANDIDATE_NEEDS_FORWARD_WEEK |
| Combined proposed shadow policy | 966 | 288 | 29.81% | 2403.84 | 0.97 | 35.07% | FAIL_TRADE_COUNT |

## Block Reason Counts

| Reason | Count |
|---|---:|
| BLOCK_WEAK_EA_ROUND_RETEST_CLONE_FAMILY | 538 |
| BLOCK_WEAK_EA_SESSION_EXTREME_RETEST | 108 |
| BLOCK_XAUUSD_MORNING_AFTERNOON | 34 |

## Duplicate-Hidden By EA

| candidate | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| swing_breakout_retest_v0 | 33 | 0 | 10 | 20 | 30.30% | 97.37 | 1.51 | 28.73 | -9.50 |
| p2weakness_br_v1 | 1 | 0 | 0 | 1 | 0.00% | -14.44 | 0.00 | n/a | -14.44 |
| symbol_normalized_round_retest_v0_repair_v1 | 1 | 0 | 0 | 1 | 0.00% | -22.23 | 0.00 | n/a | -22.23 |
| breakout_retest | 285 | 2 | 103 | 172 | 36.14% | -63.13 | 0.98 | 32.22 | -19.66 |
| round_number_retest_v0 | 21 | 1 | 8 | 13 | 38.10% | -66.12 | 0.73 | 22.26 | -18.78 |
| WR50_BreakoutEvening_v0 | 2 | 0 | 0 | 2 | 0.00% | -74.00 | 0.00 | n/a | -37.00 |
| session_extreme_retest_v0 | 108 | 0 | 28 | 69 | 25.93% | -373.23 | 0.67 | 27.53 | -16.58 |
| symbol_normalized_round_retest_v0 | 515 | 1 | 176 | 331 | 34.17% | -1982.07 | 0.80 | 43.78 | -29.26 |

## Duplicate-Hidden By Symbol

| symbol | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| USDJPY | 21 | 0 | 4 | 16 | 19.05% | -24.94 | 0.45 | 5.14 | -2.84 |
| XAUUSD | 586 | 1 | 220 | 362 | 37.54% | -554.52 | 0.95 | 45.10 | -28.94 |
| EURUSD | 202 | 0 | 61 | 129 | 30.20% | -838.88 | 0.59 | 19.87 | -15.90 |
| GBPUSD | 157 | 3 | 40 | 102 | 25.48% | -1079.51 | 0.51 | 27.65 | -21.43 |

## Duplicate-Hidden By Time Bucket

| time_bucket | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Evening 16:00-19:59 | 224 | 0 | 81 | 132 | 36.16% | -159.86 | 0.96 | 44.35 | -28.43 |
| Morning 06:00-11:59 | 213 | 3 | 72 | 139 | 33.80% | -474.59 | 0.83 | 32.89 | -20.45 |
| Night 20:00-05:59 | 386 | 1 | 137 | 238 | 35.49% | -909.23 | 0.85 | 38.64 | -26.06 |
| Afternoon 12:00-15:59 | 143 | 0 | 35 | 100 | 24.48% | -954.17 | 0.51 | 28.72 | -19.59 |

## Worst EA x Symbol x Time Clusters

| candidate | symbol | time_bucket | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| symbol_normalized_round_retest_v0 | XAUUSD | Evening 16:00-19:59 | 87 | 0 | 31 | 54 | 35.63% | -419.88 | 0.82 | 60.65 | -42.59 |
| symbol_normalized_round_retest_v0 | XAUUSD | Afternoon 12:00-15:59 | 52 | 0 | 15 | 37 | 28.85% | -373.39 | 0.63 | 42.14 | -27.18 |
| symbol_normalized_round_retest_v0 | XAUUSD | Morning 06:00-11:59 | 101 | 0 | 35 | 66 | 34.65% | -286.93 | 0.82 | 38.47 | -24.75 |
| symbol_normalized_round_retest_v0 | GBPUSD | Evening 16:00-19:59 | 22 | 0 | 3 | 18 | 13.64% | -270.39 | 0.24 | 28.70 | -19.80 |
| breakout_retest | GBPUSD | Night 20:00-05:59 | 31 | 0 | 10 | 16 | 32.26% | -267.45 | 0.49 | 25.91 | -32.91 |
| symbol_normalized_round_retest_v0 | GBPUSD | Morning 06:00-11:59 | 11 | 0 | 0 | 11 | 0.00% | -196.22 | 0.00 | n/a | -17.84 |
| symbol_normalized_round_retest_v0 | XAUUSD | Night 20:00-05:59 | 170 | 0 | 68 | 101 | 40.00% | -190.35 | 0.94 | 46.78 | -33.38 |
| breakout_retest | EURUSD | Night 20:00-05:59 | 36 | 0 | 10 | 25 | 27.78% | -169.47 | 0.56 | 21.91 | -15.54 |
| symbol_normalized_round_retest_v0 | EURUSD | Night 20:00-05:59 | 33 | 0 | 10 | 23 | 30.30% | -150.22 | 0.65 | 28.15 | -18.77 |
| session_extreme_retest_v0 | EURUSD | Evening 16:00-19:59 | 13 | 0 | 0 | 8 | 0.00% | -135.20 | 0.00 | n/a | -16.90 |
| breakout_retest | GBPUSD | Evening 16:00-19:59 | 20 | 0 | 5 | 14 | 25.00% | -134.54 | 0.46 | 23.23 | -17.91 |
| session_extreme_retest_v0 | XAUUSD | Night 20:00-05:59 | 14 | 0 | 2 | 12 | 14.29% | -131.92 | 0.40 | 44.16 | -18.35 |

## Promotion Rule

- A rule may be promoted only after it improves duplicate-hidden PF and PnL, preserves or improves win rate, keeps enough trade count, survives at least one fresh week, and receives owner/reviewer approval.
- This report is measurement-only and does not deploy a guard/router or change running EAs.
