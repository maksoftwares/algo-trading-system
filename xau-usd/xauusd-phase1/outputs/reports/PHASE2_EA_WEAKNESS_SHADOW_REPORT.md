# Phase 2 EA Weakness Shadow Report

Status: SHADOW_ONLY_NOT_ENFORCED

Measurement only. Does not change MT5 charts, EA inputs, orders, positions, presets, or runtime behavior.

Generated at UTC: `2026-06-09T12:51:59.840827Z`
History window: `2026-06-01 00:00:00` to `2026-06-09 16:51:59`
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
| Raw broker trades | 440 | 430 | 10 | 167 | 261 | 38.84% | 0.85 | 11.85 | 12.70 | 1.00 | 30.55 | -19.54 |
| Duplicate-hidden decision view | 256 | 251 | 5 | 96 | 154 | 38.25% | -72.18 | 1.85 | -70.33 | 0.97 | 28.37 | -18.15 |
| Combined shadow would keep | 88 | 87 | 1 | 40 | 47 | 45.98% | 445.98 | 0.95 | 446.93 | 1.88 | 23.86 | -10.82 |
| Combined shadow would block | 168 | 164 | 4 | 56 | 107 | 34.15% | -518.16 | 0.90 | -517.26 | 0.77 | 31.59 | -21.38 |

## Shadow Scenarios

| Scenario | Baseline Closed | Kept Closed | Kept % | Delta PnL AED | Kept PF | Kept Win Rate | Promotion Status |
|---|---:|---:|---:|---:|---:|---:|---|
| Duplicate family mutex | 430 | 251 | 58.37% | -73.03 | 0.97 | 38.25% | REJECT_OR_KEEP_MEASURING |
| EA quarantine: session_extreme_retest_v0 | 251 | 204 | 81.27% | 58.79 | 0.99 | 39.71% | SHADOW_CANDIDATE_NEEDS_FORWARD_WEEK |
| EA quarantine: symbol_normalized_round_retest_v0 | 251 | 154 | 61.35% | 383.84 | 1.25 | 38.96% | SHADOW_CANDIDATE_NEEDS_FORWARD_WEEK |
| Session filter: XAUUSD morning/afternoon | 251 | 178 | 70.92% | 364.26 | 1.18 | 41.57% | SHADOW_CANDIDATE_NEEDS_FORWARD_WEEK |
| Combined proposed shadow policy | 251 | 87 | 34.66% | 518.16 | 1.88 | 45.98% | FAIL_TRADE_COUNT |

## Block Reason Counts

| Reason | Count |
|---|---:|
| BLOCK_WEAK_EA_SYMBOL_NORMALIZED_ROUND | 101 |
| BLOCK_WEAK_EA_SESSION_EXTREME_RETEST | 47 |
| BLOCK_XAUUSD_MORNING_AFTERNOON | 20 |

## Duplicate-Hidden By EA

| candidate | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| breakout_retest | 91 | 1 | 41 | 50 | 45.05% | 428.93 | 1.65 | 26.63 | -13.26 |
| swing_breakout_retest_v0 | 12 | 0 | 4 | 8 | 33.33% | 52.19 | 3.16 | 19.09 | -3.02 |
| p2weakness_br_v1 | 1 | 0 | 0 | 1 | 0.00% | -14.44 | 0.00 | n/a | -14.44 |
| symbol_normalized_round_retest_v0_repair_v1 | 1 | 0 | 0 | 1 | 0.00% | -22.23 | 0.00 | n/a | -22.23 |
| session_extreme_retest_v0 | 47 | 0 | 15 | 32 | 31.91% | -58.79 | 0.86 | 24.73 | -13.43 |
| WR50_BreakoutEvening_v0 | 2 | 0 | 0 | 2 | 0.00% | -74.00 | 0.00 | n/a | -37.00 |
| symbol_normalized_round_retest_v0 | 97 | 4 | 36 | 60 | 37.11% | -383.84 | 0.76 | 32.90 | -26.14 |

## Duplicate-Hidden By Symbol

| symbol | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| EURUSD | 50 | 0 | 25 | 25 | 50.00% | 55.38 | 1.44 | 7.25 | -5.04 |
| GBPUSD | 4 | 2 | 2 | 2 | 50.00% | 2.75 | 1.33 | 5.53 | -4.15 |
| USDJPY | 21 | 0 | 4 | 16 | 19.05% | -24.94 | 0.45 | 5.14 | -2.84 |
| XAUUSD | 176 | 3 | 65 | 111 | 36.93% | -105.37 | 0.96 | 38.63 | -23.57 |

## Duplicate-Hidden By Time Bucket

| time_bucket | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Evening 16:00-19:59 | 49 | 4 | 25 | 24 | 51.02% | 331.30 | 1.71 | 32.04 | -19.57 |
| Night 20:00-05:59 | 96 | 0 | 35 | 61 | 36.46% | -103.87 | 0.91 | 29.51 | -18.63 |
| Afternoon 12:00-15:59 | 50 | 1 | 17 | 32 | 34.00% | -108.80 | 0.73 | 16.89 | -12.37 |
| Morning 06:00-11:59 | 56 | 0 | 19 | 37 | 33.93% | -190.81 | 0.76 | 31.73 | -21.45 |

## Worst EA x Symbol x Time Clusters

| candidate | symbol | time_bucket | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| symbol_normalized_round_retest_v0 | XAUUSD | Morning 06:00-11:59 | 36 | 0 | 13 | 23 | 36.11% | -163.30 | 0.73 | 33.58 | -26.08 |
| symbol_normalized_round_retest_v0 | XAUUSD | Afternoon 12:00-15:59 | 6 | 1 | 0 | 6 | 0.00% | -146.81 | 0.00 | n/a | -24.47 |
| session_extreme_retest_v0 | XAUUSD | Night 20:00-05:59 | 12 | 0 | 2 | 10 | 16.67% | -96.39 | 0.48 | 44.16 | -18.47 |
| WR50_BreakoutEvening_v0 | XAUUSD | Night 20:00-05:59 | 2 | 0 | 0 | 2 | 0.00% | -74.00 | 0.00 | n/a | -37.00 |
| breakout_retest | XAUUSD | Afternoon 12:00-15:59 | 8 | 0 | 2 | 6 | 25.00% | -47.34 | 0.57 | 31.98 | -18.55 |
| symbol_normalized_round_retest_v0 | XAUUSD | Evening 16:00-19:59 | 11 | 1 | 4 | 7 | 36.36% | -44.25 | 0.84 | 57.13 | -38.97 |
| symbol_normalized_round_retest_v0 | XAUUSD | Night 20:00-05:59 | 37 | 0 | 15 | 22 | 40.54% | -43.47 | 0.92 | 33.18 | -24.60 |
| session_extreme_retest_v0 | EURUSD | Evening 16:00-19:59 | 2 | 0 | 0 | 2 | 0.00% | -24.07 | 0.00 | n/a | -12.04 |
| breakout_retest | EURUSD | Night 20:00-05:59 | 12 | 0 | 4 | 8 | 33.33% | -23.42 | 0.48 | 5.50 | -5.68 |
| symbol_normalized_round_retest_v0_repair_v1 | XAUUSD | Evening 16:00-19:59 | 1 | 0 | 0 | 1 | 0.00% | -22.23 | 0.00 | n/a | -22.23 |
| p2weakness_br_v1 | XAUUSD | Morning 06:00-11:59 | 1 | 0 | 0 | 1 | 0.00% | -14.44 | 0.00 | n/a | -14.44 |
| breakout_retest | XAUUSD | Morning 06:00-11:59 | 11 | 0 | 3 | 8 | 27.27% | -13.75 | 0.92 | 49.94 | -20.45 |

## Promotion Rule

- A rule may be promoted only after it improves duplicate-hidden PF and PnL, preserves or improves win rate, keeps enough trade count, survives at least one fresh week, and receives owner/reviewer approval.
- This report is measurement-only and does not deploy a guard/router or change running EAs.
