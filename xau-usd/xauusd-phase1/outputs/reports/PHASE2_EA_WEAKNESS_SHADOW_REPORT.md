# Phase 2 EA Weakness Shadow Report

Status: SHADOW_ONLY_NOT_ENFORCED

Measurement only. Does not change MT5 charts, EA inputs, orders, positions, presets, or runtime behavior.

Generated at UTC: `2026-06-12T09:19:07.276349Z`
History window: `2026-06-01 00:00:00` to `2026-06-12 13:19:07`
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
| Raw broker trades | 1372 | 1356 | 16 | 499 | 824 | 36.80% | 61.93 | 211.20 | 273.13 | 1.00 | 43.82 | -26.46 |
| Duplicate-hidden decision view | 731 | 722 | 9 | 254 | 452 | 35.18% | -1270.93 | 111.88 | -1159.05 | 0.89 | 38.89 | -24.67 |
| Combined shadow would keep | 206 | 201 | 5 | 73 | 124 | 36.32% | 97.97 | -23.16 | 74.81 | 1.04 | 31.72 | -17.88 |
| Combined shadow would block | 525 | 521 | 4 | 181 | 328 | 34.74% | -1368.90 | 135.04 | -1233.86 | 0.85 | 41.78 | -27.23 |

## Shadow Scenarios

| Scenario | Baseline Closed | Kept Closed | Kept % | Delta PnL AED | Kept PF | Kept Win Rate | Promotion Status |
|---|---:|---:|---:|---:|---:|---:|---|
| Duplicate family mutex | 1356 | 722 | 53.24% | -1332.86 | 0.89 | 35.18% | REJECT_OR_KEEP_MEASURING |
| EA quarantine: session_extreme_retest_v0 | 722 | 635 | 87.95% | 170.60 | 0.89 | 35.91% | SHADOW_CANDIDATE_NEEDS_FORWARD_WEEK |
| EA quarantine: symbol_normalized_round_retest_v0 | 722 | 321 | 44.46% | 1197.70 | 0.98 | 34.27% | REJECT_OR_KEEP_MEASURING |
| EA quarantine: round_number_retest_v0 | 722 | 719 | 99.58% | -11.76 | 0.88 | 35.19% | REJECT_OR_KEEP_MEASURING |
| Family quarantine: round-retest clone family | 722 | 318 | 44.04% | 1185.94 | 0.98 | 34.28% | REJECT_OR_KEEP_MEASURING |
| Session filter: XAUUSD morning/afternoon | 722 | 561 | 77.70% | 298.65 | 0.89 | 35.29% | SHADOW_CANDIDATE_NEEDS_FORWARD_WEEK |
| Combined proposed shadow policy | 722 | 201 | 27.84% | 1368.90 | 1.04 | 36.32% | FAIL_TRADE_COUNT |

## Block Reason Counts

| Reason | Count |
|---|---:|
| BLOCK_WEAK_EA_ROUND_RETEST_CLONE_FAMILY | 406 |
| BLOCK_WEAK_EA_SESSION_EXTREME_RETEST | 89 |
| BLOCK_XAUUSD_MORNING_AFTERNOON | 30 |

## Duplicate-Hidden By EA

| candidate | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| breakout_retest | 212 | 5 | 78 | 130 | 36.79% | 153.30 | 1.06 | 33.28 | -18.79 |
| swing_breakout_retest_v0 | 15 | 0 | 5 | 10 | 33.33% | 42.98 | 1.70 | 20.85 | -6.13 |
| round_number_retest_v0 | 3 | 0 | 1 | 2 | 33.33% | 11.76 | 1.38 | 42.59 | -15.41 |
| p2weakness_br_v1 | 1 | 0 | 0 | 1 | 0.00% | -14.44 | 0.00 | n/a | -14.44 |
| symbol_normalized_round_retest_v0_repair_v1 | 1 | 0 | 0 | 1 | 0.00% | -22.23 | 0.00 | n/a | -22.23 |
| WR50_BreakoutEvening_v0 | 2 | 0 | 0 | 2 | 0.00% | -74.00 | 0.00 | n/a | -37.00 |
| session_extreme_retest_v0 | 87 | 2 | 26 | 55 | 29.89% | -170.60 | 0.81 | 27.52 | -16.11 |
| symbol_normalized_round_retest_v0 | 401 | 2 | 144 | 251 | 35.91% | -1197.70 | 0.84 | 44.58 | -30.35 |

## Duplicate-Hidden By Symbol

| symbol | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| USDJPY | 21 | 0 | 4 | 16 | 19.05% | -24.94 | 0.45 | 5.14 | -2.84 |
| XAUUSD | 449 | 2 | 170 | 275 | 37.86% | -119.17 | 0.99 | 47.91 | -30.05 |
| EURUSD | 148 | 3 | 50 | 92 | 33.78% | -506.82 | 0.63 | 17.62 | -15.08 |
| GBPUSD | 104 | 4 | 30 | 69 | 28.85% | -620.00 | 0.57 | 27.72 | -21.04 |

## Duplicate-Hidden By Time Bucket

| time_bucket | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Evening 16:00-19:59 | 170 | 0 | 66 | 93 | 38.82% | 172.99 | 1.06 | 43.97 | -29.34 |
| Afternoon 12:00-15:59 | 99 | 7 | 29 | 69 | 29.29% | -384.19 | 0.68 | 28.23 | -17.43 |
| Morning 06:00-11:59 | 159 | 0 | 53 | 106 | 33.33% | -487.84 | 0.79 | 34.82 | -22.01 |
| Night 20:00-05:59 | 294 | 2 | 106 | 184 | 36.05% | -571.89 | 0.88 | 40.68 | -26.54 |

## Worst EA x Symbol x Time Clusters

| candidate | symbol | time_bucket | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| symbol_normalized_round_retest_v0 | XAUUSD | Evening 16:00-19:59 | 66 | 0 | 23 | 41 | 34.85% | -398.64 | 0.78 | 61.74 | -44.36 |
| symbol_normalized_round_retest_v0 | XAUUSD | Morning 06:00-11:59 | 86 | 0 | 32 | 54 | 37.21% | -190.06 | 0.87 | 38.47 | -26.32 |
| symbol_normalized_round_retest_v0 | XAUUSD | Night 20:00-05:59 | 143 | 0 | 56 | 86 | 39.16% | -182.43 | 0.94 | 48.95 | -33.99 |
| breakout_retest | GBPUSD | Night 20:00-05:59 | 23 | 2 | 8 | 13 | 34.78% | -168.13 | 0.55 | 25.53 | -28.64 |
| breakout_retest | GBPUSD | Morning 06:00-11:59 | 19 | 0 | 4 | 15 | 21.05% | -165.02 | 0.40 | 27.95 | -18.46 |
| symbol_normalized_round_retest_v0 | GBPUSD | Evening 16:00-19:59 | 17 | 0 | 3 | 13 | 17.65% | -155.39 | 0.36 | 28.70 | -18.58 |
| symbol_normalized_round_retest_v0 | GBPUSD | Morning 06:00-11:59 | 7 | 0 | 0 | 7 | 0.00% | -133.18 | 0.00 | n/a | -19.03 |
| breakout_retest | EURUSD | Morning 06:00-11:59 | 12 | 0 | 2 | 10 | 16.67% | -129.58 | 0.08 | 5.51 | -14.06 |
| session_extreme_retest_v0 | EURUSD | Evening 16:00-19:59 | 12 | 0 | 0 | 7 | 0.00% | -116.83 | 0.00 | n/a | -16.69 |
| session_extreme_retest_v0 | XAUUSD | Night 20:00-05:59 | 13 | 0 | 2 | 11 | 15.38% | -112.89 | 0.44 | 44.16 | -18.29 |
| breakout_retest | EURUSD | Afternoon 12:00-15:59 | 17 | 1 | 4 | 13 | 23.53% | -94.76 | 0.32 | 11.03 | -10.68 |
| breakout_retest | EURUSD | Night 20:00-05:59 | 25 | 0 | 8 | 17 | 32.00% | -87.15 | 0.61 | 17.06 | -13.15 |

## Promotion Rule

- A rule may be promoted only after it improves duplicate-hidden PF and PnL, preserves or improves win rate, keeps enough trade count, survives at least one fresh week, and receives owner/reviewer approval.
- This report is measurement-only and does not deploy a guard/router or change running EAs.
