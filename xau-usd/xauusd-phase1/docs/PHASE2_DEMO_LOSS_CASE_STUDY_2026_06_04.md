# Phase 2 Demo Loss Case Study - Actual MT5 Trades

Generated at: 2026-06-04 17:46:50 Asia/Dubai local system time
Source terminal: `C:\Program Files\MetaTrader 5\terminal64.exe`
Account: `1025742 / Capital.ComMena-Demo / AED`
History window: `2026-06-01 00:00:00` to `2026-06-04 17:46:50`

This study uses direct MT5 history, groups entry/exit deals into trades, and marks same-minute same-symbol same-side duplicate families. The duplicate-hidden baseline is the main decision view.

## Executive Findings

- Duplicate-hidden baseline: 125 closed trades, 48 wins, 77 losses, win rate 38.40%, closed PnL -56.41 AED, PF 0.96.
- Raw actual grouped orders: 211 closed trades, PnL -222.01 AED. Raw order-level evidence is less clean because duplicate same-family entries amplify both wins and losses.
- The primary loss driver is not broker charges in this demo sample; losses are mainly stop-loss outcomes from selection/timing.
- Shadow filter impact if only measured, not enforced: kept PnL 318.11 AED versus baseline -56.41 AED, delta 374.52 AED.
- The worst clusters remain XAUUSD morning/afternoon and `symbol_normalized_round_retest_v0`; `breakout_retest` is positive overall and strongest in evening XAUUSD.

## Overall

| View | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Raw grouped MT5 trades | 211 | 4 | 79 | 132 | 37.44% | -222.01 | 0.91 | 28.37 | -18.66 |
| Duplicate-hidden baseline | 125 | 2 | 48 | 77 | 38.40% | -56.41 | 0.96 | 27.12 | -17.64 |
| Shadow kept subset | 61 | 2 | 29 | 32 | 47.54% | 318.11 | 1.62 | 28.73 | -16.10 |
| Shadow blocked subset | 64 | 0 | 19 | 45 | 29.69% | -374.52 | 0.56 | 24.65 | -18.73 |

## By EA

| candidate | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| breakout_retest | 40 | 2 | 18 | 22 | 45.00% | 248.45 | 1.95 | 28.40 | -11.94 |
| swing_breakout_retest_v0 | 3 | 0 | 1 | 2 | 33.33% | 60.80 | 20.49 | 63.92 | -1.56 |
| session_extreme_retest_v0 | 32 | 0 | 11 | 21 | 34.38% | -28.21 | 0.90 | 22.63 | -13.20 |
| symbol_normalized_round_retest_v0 | 50 | 0 | 18 | 32 | 36.00% | -337.45 | 0.59 | 26.53 | -25.47 |

## By Symbol

| symbol | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| EURUSD | 23 | 1 | 11 | 12 | 47.83% | 15.12 | 1.34 | 5.47 | -3.75 |
| USDJPY | 8 | 1 | 2 | 6 | 25.00% | -9.33 | 0.25 | 1.59 | -2.09 |
| XAUUSD | 94 | 0 | 35 | 59 | 37.23% | -62.20 | 0.95 | 35.38 | -22.04 |

## By Time Bucket

| time_bucket | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Evening 16:00-19:59 | 21 | 0 | 12 | 9 | 57.14% | 216.01 | 2.05 | 35.08 | -22.77 |
| Night 20:00-05:59 | 45 | 0 | 18 | 27 | 40.00% | 58.26 | 1.13 | 28.89 | -17.10 |
| Afternoon 12:00-15:59 | 33 | 2 | 10 | 23 | 30.30% | -89.42 | 0.68 | 19.41 | -12.33 |
| Morning 06:00-11:59 | 26 | 0 | 8 | 18 | 30.77% | -241.26 | 0.41 | 20.80 | -22.65 |

## EA x Time Bucket

| candidate | time_bucket | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| breakout_retest | Evening 16:00-19:59 | 7 | 0 | 6 | 1 | 85.71% | 213.64 | 9.72 | 39.69 | -24.51 |
| breakout_retest | Night 20:00-05:59 | 15 | 0 | 6 | 9 | 40.00% | 77.10 | 1.80 | 28.86 | -10.67 |
| swing_breakout_retest_v0 | Evening 16:00-19:59 | 2 | 0 | 1 | 1 | 50.00% | 61.95 | 32.45 | 63.92 | -1.97 |
| symbol_normalized_round_retest_v0 | Night 20:00-05:59 | 19 | 0 | 9 | 10 | 47.37% | 40.32 | 1.16 | 31.75 | -24.54 |
| session_extreme_retest_v0 | Afternoon 12:00-15:59 | 16 | 0 | 6 | 10 | 37.50% | 20.64 | 1.20 | 20.53 | -10.25 |
| session_extreme_retest_v0 | Evening 16:00-19:59 | 5 | 0 | 2 | 3 | 40.00% | 10.31 | 1.19 | 32.33 | -18.11 |
| swing_breakout_retest_v0 | Afternoon 12:00-15:59 | 1 | 0 | 0 | 1 | 0.00% | -1.15 | 0.00 | n/a | -1.15 |
| breakout_retest | Morning 06:00-11:59 | 5 | 0 | 2 | 3 | 40.00% | -1.21 | 0.96 | 14.46 | -10.05 |
| breakout_retest | Afternoon 12:00-15:59 | 13 | 2 | 4 | 9 | 30.77% | -41.08 | 0.63 | 17.73 | -12.45 |
| session_extreme_retest_v0 | Night 20:00-05:59 | 11 | 0 | 3 | 8 | 27.27% | -59.16 | 0.51 | 20.39 | -15.04 |
| symbol_normalized_round_retest_v0 | Afternoon 12:00-15:59 | 3 | 0 | 0 | 3 | 0.00% | -67.83 | 0.00 | n/a | -22.61 |
| symbol_normalized_round_retest_v0 | Evening 16:00-19:59 | 7 | 0 | 3 | 4 | 42.86% | -69.89 | 0.44 | 18.09 | -31.04 |
| symbol_normalized_round_retest_v0 | Morning 06:00-11:59 | 21 | 0 | 6 | 15 | 28.57% | -240.05 | 0.36 | 22.92 | -25.17 |

## Worst EA x Symbol x Time Clusters

| candidate | symbol | time_bucket | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| symbol_normalized_round_retest_v0 | XAUUSD | Morning 06:00-11:59 | 20 | 0 | 5 | 15 | 25.00% | -245.56 | 0.35 | 26.40 | -25.17 |
| symbol_normalized_round_retest_v0 | XAUUSD | Evening 16:00-19:59 | 5 | 0 | 1 | 4 | 20.00% | -80.50 | 0.35 | 43.65 | -31.04 |
| symbol_normalized_round_retest_v0 | XAUUSD | Afternoon 12:00-15:59 | 3 | 0 | 0 | 3 | 0.00% | -67.83 | 0.00 | n/a | -22.61 |
| session_extreme_retest_v0 | XAUUSD | Night 20:00-05:59 | 7 | 0 | 1 | 6 | 14.29% | -64.71 | 0.44 | 50.19 | -19.15 |
| breakout_retest | XAUUSD | Afternoon 12:00-15:59 | 7 | 0 | 2 | 5 | 28.57% | -33.45 | 0.66 | 31.98 | -19.48 |
| breakout_retest | EURUSD | Afternoon 12:00-15:59 | 5 | 1 | 1 | 4 | 20.00% | -9.10 | 0.38 | 5.51 | -3.65 |
| breakout_retest | EURUSD | Night 20:00-05:59 | 6 | 0 | 2 | 4 | 33.33% | -4.52 | 0.71 | 5.51 | -3.88 |
| session_extreme_retest_v0 | EURUSD | Evening 16:00-19:59 | 1 | 0 | 0 | 1 | 0.00% | -3.64 | 0.00 | n/a | -3.64 |
| breakout_retest | USDJPY | Morning 06:00-11:59 | 1 | 0 | 0 | 1 | 0.00% | -3.50 | 0.00 | n/a | -3.50 |
| session_extreme_retest_v0 | USDJPY | Afternoon 12:00-15:59 | 3 | 0 | 1 | 2 | 33.33% | -2.58 | 0.40 | 1.72 | -2.15 |
| swing_breakout_retest_v0 | USDJPY | Evening 16:00-19:59 | 1 | 0 | 0 | 1 | 0.00% | -1.97 | 0.00 | n/a | -1.97 |
| session_extreme_retest_v0 | USDJPY | Night 20:00-05:59 | 1 | 0 | 0 | 1 | 0.00% | -1.60 | 0.00 | n/a | -1.60 |

## Largest Individual Losses

| Entry | Exit | EA | Symbol | Direction | Time Bucket | PnL AED | Duplicate Role | Exit |
|---|---|---|---|---|---|---:|---|---|
| 2026-06-01 17:40:00 | 2026-06-01 17:51:25 | symbol_normalized_round_retest_v0 | XAUUSD | BUY | Evening 16:00-19:59 | -45.78 | kept | [sl 4461.22] |
| 2026-06-02 05:55:00 | 2026-06-02 06:23:58 | symbol_normalized_round_retest_v0 | XAUUSD | SELL | Night 20:00-05:59 | -42.33 | kept | [sl 4484.82] |
| 2026-06-03 09:40:00 | 2026-06-03 09:59:10 | symbol_normalized_round_retest_v0 | XAUUSD | BUY | Morning 06:00-11:59 | -38.43 | kept | [sl 4456.86] |
| 2026-06-04 06:00:00 | 2026-06-04 06:10:15 | symbol_normalized_round_retest_v0 | XAUUSD | BUY | Morning 06:00-11:59 | -37.00 | kept | [sl 4456.65] |
| 2026-06-02 05:25:00 | 2026-06-02 05:29:17 | session_extreme_retest_v0 | XAUUSD | SELL | Night 20:00-05:59 | -35.53 | unique | [sl 4492.16] |
| 2026-06-03 05:15:00 | 2026-06-03 06:13:04 | symbol_normalized_round_retest_v0 | XAUUSD | SELL | Night 20:00-05:59 | -32.96 | kept | [sl 4480.09] |
| 2026-06-01 16:40:01 | 2026-06-01 17:03:44 | symbol_normalized_round_retest_v0 | XAUUSD | BUY | Evening 16:00-19:59 | -31.05 | kept | [sl 4495.67] |
| 2026-06-04 11:25:00 | 2026-06-04 13:52:03 | symbol_normalized_round_retest_v0 | XAUUSD | SELL | Morning 06:00-11:59 | -30.35 | kept | [sl 4474.10] |
| 2026-06-04 08:20:00 | 2026-06-04 10:47:22 | symbol_normalized_round_retest_v0 | XAUUSD | BUY | Morning 06:00-11:59 | -29.80 | kept | [sl 4464.18] |
| 2026-06-04 02:20:00 | 2026-06-04 02:27:26 | breakout_retest | XAUUSD | SELL | Night 20:00-05:59 | -28.07 | kept | [sl 4434.52] |
| 2026-06-04 06:50:00 | 2026-06-04 07:40:33 | symbol_normalized_round_retest_v0 | XAUUSD | BUY | Morning 06:00-11:59 | -27.67 | kept | [sl 4463.32] |
| 2026-06-03 18:20:00 | 2026-06-03 18:49:19 | session_extreme_retest_v0 | XAUUSD | SELL | Evening 16:00-19:59 | -27.41 | unique | [sl 4455.02] |
| 2026-06-04 04:15:01 | 2026-06-04 05:10:02 | symbol_normalized_round_retest_v0 | XAUUSD | SELL | Night 20:00-05:59 | -26.68 | kept | [sl 4460.32] |
| 2026-06-03 06:25:01 | 2026-06-03 08:39:18 | symbol_normalized_round_retest_v0 | XAUUSD | BUY | Morning 06:00-11:59 | -26.56 | kept | [sl 4471.07] |
| 2026-06-04 11:15:00 | 2026-06-04 11:19:07 | symbol_normalized_round_retest_v0 | XAUUSD | SELL | Morning 06:00-11:59 | -25.64 | kept | [sl 4470.93] |

## Interpretation

The loss pattern is mostly a filtering problem, not a broker-cost-only problem. The same strategies perform very differently by time bucket and symbol. Evening/night XAUUSD has been profitable, while morning/afternoon XAUUSD has been the main drag. This report now includes a shadow-only policy so the weak clusters can be measured without changing the running EAs.

Recommended operating stance: keep execution unchanged for the planned observation window, but review the shadow filter delta daily. Do not enforce it until it survives a larger sample.
