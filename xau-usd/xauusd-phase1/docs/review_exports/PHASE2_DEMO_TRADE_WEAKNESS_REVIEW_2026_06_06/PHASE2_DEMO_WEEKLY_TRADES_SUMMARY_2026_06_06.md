# Phase 2 Demo Weekly Trades Summary - 2026_06_06

This packet is actual demo broker trade evidence for reviewer inspection.

- History start: `2026-06-01 00:00:00`
- Source: refreshed MT5 broker-history export written to `outputs/reports/PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv`.
- Boundary: experimental demo evidence only; not canonical Phase 2 evidence and not live-trading authorization.
- Duplicate rows marked: `127`.

## Overall

| View | Total | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | Floating AED | Net AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Raw broker trades | 305 | 301 | 4 | 119 | 182 | 39.53% | 89.55 | 33.72 | 123.27 | 1.03 | 28.90 | -18.40 |
| Duplicate-hidden unique trades | 178 | 176 | 2 | 69 | 107 | 39.20% | 53.70 | 16.86 | 70.56 | 1.03 | 27.61 | -17.30 |

## Unique Trades by Symbol

| symbol | Total | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | Floating AED | Net AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| XAUUSD | 127 | 127 | 0 | 48 | 79 | 37.80% | 42.38 | 0.00 | 42.38 | 1.02 | 37.53 | -22.27 |
| EURUSD | 34 | 34 | 0 | 18 | 16 | 52.94% | 37.35 | 0.00 | 37.35 | 1.61 | 5.48 | -3.83 |
| USDJPY | 17 | 15 | 2 | 3 | 12 | 20.00% | -26.03 | 16.86 | -9.17 | 0.15 | 1.55 | -2.56 |

## Unique Trades by Candidate

| candidate | Total | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | Floating AED | Net AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| breakout_retest | 66 | 65 | 1 | 31 | 34 | 47.69% | 384.00 | 13.10 | 397.10 | 1.85 | 26.91 | -13.24 |
| swing_breakout_retest_v0 | 8 | 8 | 0 | 3 | 5 | 37.50% | 60.37 | 0.00 | 60.37 | 6.76 | 23.62 | -2.10 |
| session_extreme_retest_v0 | 40 | 39 | 1 | 12 | 27 | 30.77% | -81.73 | 3.76 | -77.97 | 0.76 | 21.21 | -12.45 |
| symbol_normalized_round_retest_v0 | 64 | 64 | 0 | 23 | 41 | 35.94% | -308.94 | 0.00 | -308.94 | 0.71 | 32.40 | -25.71 |

## Unique Trades by Time Bucket

| time_bucket | Total | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | Floating AED | Net AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Evening 16:00-19:59 | 38 | 37 | 1 | 22 | 15 | 59.46% | 399.52 | 3.76 | 403.28 | 2.38 | 31.33 | -19.31 |
| Afternoon 12:00-15:59 | 36 | 35 | 1 | 10 | 25 | 28.57% | -97.65 | 13.10 | -84.55 | 0.67 | 19.41 | -11.67 |
| Night 20:00-05:59 | 69 | 69 | 0 | 24 | 45 | 34.78% | -101.42 | 0.00 | -101.42 | 0.87 | 28.34 | -17.37 |
| Morning 06:00-11:59 | 35 | 35 | 0 | 13 | 22 | 37.14% | -146.75 | 0.00 | -146.75 | 0.70 | 26.25 | -22.18 |

## Unique Trades by Candidate and Symbol

| candidate | symbol | Total | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | Floating AED | Net AED | PF | Avg Win | Avg Loss |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| breakout_retest | XAUUSD | 41 | 41 | 0 | 20 | 21 | 48.78% | 377.49 | 0.00 | 377.49 | 1.94 | 38.89 | -19.06 |
| swing_breakout_retest_v0 | XAUUSD | 1 | 1 | 0 | 1 | 0 | 100.00% | 63.92 | 0.00 | 63.92 | inf | 63.92 | n/a |
| symbol_normalized_round_retest_v0 | EURUSD | 4 | 4 | 0 | 3 | 1 | 75.00% | 12.48 | 0.00 | 12.48 | 4.43 | 5.37 | -3.64 |
| session_extreme_retest_v0 | EURUSD | 7 | 7 | 0 | 4 | 3 | 57.14% | 10.86 | 0.00 | 10.86 | 1.97 | 5.50 | -3.71 |
| breakout_retest | EURUSD | 22 | 22 | 0 | 10 | 12 | 45.45% | 8.54 | 0.00 | 8.54 | 1.18 | 5.51 | -3.88 |
| swing_breakout_retest_v0 | EURUSD | 1 | 1 | 0 | 1 | 0 | 100.00% | 5.47 | 0.00 | 5.47 | inf | 5.47 | n/a |
| breakout_retest | USDJPY | 3 | 2 | 1 | 1 | 1 | 50.00% | -2.03 | 13.10 | 11.07 | 0.42 | 1.47 | -3.50 |
| swing_breakout_retest_v0 | USDJPY | 6 | 6 | 0 | 1 | 5 | 16.67% | -9.02 | 0.00 | -9.02 | 0.14 | 1.47 | -2.10 |
| session_extreme_retest_v0 | USDJPY | 8 | 7 | 1 | 1 | 6 | 14.29% | -14.98 | 3.76 | -11.22 | 0.10 | 1.72 | -2.78 |
| session_extreme_retest_v0 | XAUUSD | 25 | 25 | 0 | 7 | 18 | 28.00% | -77.61 | 0.00 | -77.61 | 0.75 | 32.97 | -17.13 |
| symbol_normalized_round_retest_v0 | XAUUSD | 60 | 60 | 0 | 20 | 40 | 33.33% | -321.42 | 0.00 | -321.42 | 0.69 | 36.45 | -26.26 |
