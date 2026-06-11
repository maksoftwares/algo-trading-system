# Phase 2 Demo Weekly Trades Summary - 2026_06_10

This packet is actual demo broker trade evidence for reviewer inspection.

- History start: `2026-06-09 00:00:00`
- Source: refreshed MT5 broker-history export written to `outputs/reports/PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv`.
- Boundary: experimental demo evidence only; not canonical Phase 2 evidence and not live-trading authorization.
- Duplicate rows marked: `247`.

## Overall

| View | Total | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | Floating AED | Net AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Raw broker trades | 565 | 545 | 20 | 209 | 334 | 38.35% | 720.84 | -81.46 | 639.38 | 1.10 | 36.72 | -20.82 |
| Duplicate-hidden unique trades | 318 | 305 | 13 | 110 | 194 | 36.07% | -329.65 | -18.77 | -348.42 | 0.91 | 31.35 | -19.47 |

## Unique Trades by Symbol

| symbol | Total | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | Floating AED | Net AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| USDJPY | 21 | 21 | 0 | 4 | 16 | 19.05% | -24.94 | 0.00 | -24.94 | 0.45 | 5.14 | -2.84 |
| GBPUSD | 17 | 15 | 2 | 5 | 10 | 33.33% | -62.35 | -2.57 | -64.92 | 0.61 | 19.54 | -16.01 |
| EURUSD | 68 | 61 | 7 | 26 | 35 | 42.62% | -102.82 | 29.37 | -73.45 | 0.67 | 8.03 | -8.91 |
| XAUUSD | 212 | 208 | 4 | 75 | 133 | 36.06% | -139.54 | -45.57 | -185.11 | 0.96 | 41.62 | -24.52 |

## Unique Trades by Candidate

| candidate | Total | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | Floating AED | Net AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| breakout_retest | 106 | 103 | 3 | 46 | 57 | 44.66% | 567.81 | -16.68 | 551.13 | 1.70 | 29.95 | -14.21 |
| swing_breakout_retest_v0 | 12 | 12 | 0 | 4 | 8 | 33.33% | 52.19 | 0.00 | 52.19 | 3.16 | 19.09 | -3.02 |
| p2weakness_br_v1 | 1 | 1 | 0 | 0 | 1 | 0.00% | -14.44 | 0.00 | -14.44 | 0.00 | n/a | -14.44 |
| symbol_normalized_round_retest_v0_repair_v1 | 1 | 1 | 0 | 0 | 1 | 0.00% | -22.23 | 0.00 | -22.23 | 0.00 | n/a | -22.23 |
| WR50_BreakoutEvening_v0 | 2 | 2 | 0 | 0 | 2 | 0.00% | -74.00 | 0.00 | -74.00 | 0.00 | n/a | -37.00 |
| session_extreme_retest_v0 | 56 | 55 | 1 | 15 | 40 | 27.27% | -208.52 | -9.00 | -217.52 | 0.64 | 24.73 | -14.49 |
| symbol_normalized_round_retest_v0 | 140 | 131 | 9 | 45 | 85 | 34.35% | -630.46 | 6.91 | -623.55 | 0.72 | 36.07 | -26.51 |

## Unique Trades by Time Bucket

| time_bucket | Total | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | Floating AED | Net AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Evening 16:00-19:59 | 76 | 76 | 0 | 35 | 41 | 46.05% | 426.35 | 0.00 | 426.35 | 1.47 | 37.87 | -21.93 |
| Afternoon 12:00-15:59 | 51 | 51 | 0 | 17 | 33 | 33.33% | -134.33 | 0.00 | -134.33 | 0.68 | 16.89 | -12.77 |
| Morning 06:00-11:59 | 56 | 56 | 0 | 19 | 37 | 33.93% | -190.81 | 0.00 | -190.81 | 0.76 | 31.73 | -21.45 |
| Night 20:00-05:59 | 135 | 122 | 13 | 39 | 83 | 31.97% | -430.86 | -18.77 | -449.63 | 0.74 | 31.62 | -20.05 |

## Unique Trades by Candidate and Symbol

| candidate | symbol | Total | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | Floating AED | Net AED | PF | Avg Win | Avg Loss |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| breakout_retest | XAUUSD | 59 | 58 | 1 | 26 | 32 | 44.83% | 538.04 | -14.11 | 523.93 | 1.82 | 45.96 | -20.53 |
| swing_breakout_retest_v0 | XAUUSD | 1 | 1 | 0 | 1 | 0 | 100.00% | 63.92 | 0.00 | 63.92 | inf | 63.92 | n/a |
| breakout_retest | EURUSD | 34 | 34 | 0 | 15 | 19 | 44.12% | 25.25 | 0.00 | 25.25 | 1.25 | 8.45 | -5.34 |
| breakout_retest | USDJPY | 5 | 5 | 0 | 2 | 3 | 40.00% | 9.04 | 0.00 | 9.04 | 2.08 | 8.69 | -2.78 |
| swing_breakout_retest_v0 | EURUSD | 4 | 4 | 0 | 2 | 2 | 50.00% | 3.56 | 0.00 | 3.56 | 1.48 | 5.49 | -3.71 |
| symbol_normalized_round_retest_v0 | USDJPY | 1 | 1 | 0 | 0 | 0 | 0.00% | 0.00 | 0.00 | 0.00 | n/a | n/a | n/a |
| breakout_retest | GBPUSD | 8 | 6 | 2 | 3 | 3 | 50.00% | -4.52 | -2.57 | -7.09 | 0.90 | 12.92 | -14.43 |
| p2weakness_br_v1 | XAUUSD | 1 | 1 | 0 | 0 | 1 | 0.00% | -14.44 | 0.00 | -14.44 | 0.00 | n/a | -14.44 |
| swing_breakout_retest_v0 | USDJPY | 7 | 7 | 0 | 1 | 6 | 14.29% | -15.29 | 0.00 | -15.29 | 0.09 | 1.47 | -2.79 |
| symbol_normalized_round_retest_v0 | EURUSD | 13 | 7 | 6 | 4 | 3 | 57.14% | -18.61 | 38.37 | 19.76 | 0.54 | 5.40 | -13.40 |
| session_extreme_retest_v0 | USDJPY | 8 | 8 | 0 | 1 | 7 | 12.50% | -18.69 | 0.00 | -18.69 | 0.08 | 1.72 | -2.92 |
| session_extreme_retest_v0 | GBPUSD | 1 | 1 | 0 | 0 | 1 | 0.00% | -18.74 | 0.00 | -18.74 | 0.00 | n/a | -18.74 |
| symbol_normalized_round_retest_v0_repair_v1 | XAUUSD | 1 | 1 | 0 | 0 | 1 | 0.00% | -22.23 | 0.00 | -22.23 | 0.00 | n/a | -22.23 |
| symbol_normalized_round_retest_v0 | GBPUSD | 8 | 8 | 0 | 2 | 6 | 25.00% | -39.09 | 0.00 | -39.09 | 0.60 | 29.46 | -16.34 |
| session_extreme_retest_v0 | XAUUSD | 30 | 30 | 0 | 9 | 21 | 30.00% | -58.07 | 0.00 | -58.07 | 0.85 | 35.52 | -17.99 |
| WR50_BreakoutEvening_v0 | XAUUSD | 2 | 2 | 0 | 0 | 2 | 0.00% | -74.00 | 0.00 | -74.00 | 0.00 | n/a | -37.00 |
| session_extreme_retest_v0 | EURUSD | 17 | 16 | 1 | 5 | 11 | 31.25% | -113.02 | -9.00 | -122.02 | 0.30 | 9.91 | -14.78 |
| symbol_normalized_round_retest_v0 | XAUUSD | 118 | 115 | 3 | 39 | 76 | 33.91% | -572.76 | -31.46 | -604.22 | 0.73 | 39.56 | -27.83 |
