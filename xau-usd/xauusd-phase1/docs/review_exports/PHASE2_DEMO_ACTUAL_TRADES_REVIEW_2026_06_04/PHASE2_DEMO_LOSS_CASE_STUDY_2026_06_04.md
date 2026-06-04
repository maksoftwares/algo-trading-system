# Phase 2 Demo Loss Case Study - Actual MT5 Trades

Generated at: 2026-06-04 11:03:11 Asia/Dubai local system time
Source terminal: `C:\Program Files\MetaTrader 5\terminal64.exe`
Account: `1025742 / Capital.ComMena-Demo / AED`
History window: `2026-06-01 00:00:00` to `2026-06-04 11:03:11`

This study uses direct MT5 history, groups entry/exit deals into trades, and marks same-minute same-symbol same-side duplicate families. The duplicate-hidden baseline is the main decision view.

## Executive Findings

- Duplicate-hidden baseline: 116 closed trades, 43 wins, 73 losses, win rate 37.07%, closed PnL -135.38 AED, PF 0.90.
- Raw actual grouped orders: 197 closed trades, PnL -299.67 AED. Raw order-level evidence is less clean because duplicate same-family entries amplify both wins and losses.
- The primary loss driver is not broker charges in this demo sample; losses are mainly stop-loss outcomes from selection/timing.
- Shadow filter impact if only measured, not enforced: kept PnL 279.86 AED versus baseline -135.38 AED, delta 415.24 AED.
- The worst clusters remain XAUUSD morning/afternoon and `symbol_normalized_round_retest_v0`; `breakout_retest` is positive overall and strongest in evening XAUUSD.

## Overall

| View | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Raw grouped MT5 trades | 197 | 5 | 72 | 125 | 36.55% | -299.67 | 0.87 | 28.37 | -18.74 |
| Duplicate-hidden baseline | 116 | 3 | 43 | 73 | 37.07% | -135.38 | 0.90 | 27.02 | -17.77 |
| Shadow kept subset | 57 | 2 | 27 | 30 | 47.37% | 279.86 | 1.55 | 29.26 | -17.01 |
| Shadow blocked subset | 59 | 1 | 16 | 43 | 27.12% | -415.24 | 0.47 | 23.23 | -18.30 |

## By EA

| candidate | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| breakout_retest | 37 | 1 | 16 | 21 | 43.24% | 179.93 | 1.69 | 27.44 | -12.34 |
| swing_breakout_retest_v0 | 2 | 0 | 1 | 1 | 50.00% | 61.95 | 32.45 | 63.92 | -1.97 |
| session_extreme_retest_v0 | 31 | 0 | 10 | 21 | 32.26% | -66.47 | 0.76 | 21.07 | -13.20 |
| symbol_normalized_round_retest_v0 | 46 | 2 | 16 | 30 | 34.78% | -310.79 | 0.59 | 28.01 | -25.30 |

## By Symbol

| symbol | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| EURUSD | 21 | 1 | 10 | 11 | 47.62% | 13.69 | 1.33 | 5.51 | -3.76 |
| USDJPY | 7 | 1 | 2 | 5 | 28.57% | -8.18 | 0.28 | 1.59 | -2.27 |
| XAUUSD | 88 | 1 | 31 | 57 | 35.23% | -140.89 | 0.89 | 35.60 | -21.83 |

## By Time Bucket

| time_bucket | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Evening 16:00-19:59 | 19 | 1 | 10 | 9 | 52.63% | 172.94 | 1.84 | 37.79 | -22.77 |
| Night 20:00-05:59 | 45 | 0 | 18 | 27 | 40.00% | 58.26 | 1.13 | 28.89 | -17.10 |
| Afternoon 12:00-15:59 | 29 | 1 | 8 | 21 | 27.59% | -157.08 | 0.44 | 15.20 | -13.27 |
| Morning 06:00-11:59 | 23 | 1 | 7 | 16 | 30.43% | -209.50 | 0.40 | 20.31 | -21.98 |

## EA x Time Bucket

| candidate | time_bucket | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| breakout_retest | Evening 16:00-19:59 | 6 | 0 | 5 | 1 | 83.33% | 175.67 | 8.17 | 40.04 | -24.51 |
| breakout_retest | Night 20:00-05:59 | 15 | 0 | 6 | 9 | 40.00% | 77.10 | 1.80 | 28.86 | -10.67 |
| swing_breakout_retest_v0 | Evening 16:00-19:59 | 2 | 0 | 1 | 1 | 50.00% | 61.95 | 32.45 | 63.92 | -1.97 |
| symbol_normalized_round_retest_v0 | Night 20:00-05:59 | 19 | 0 | 9 | 10 | 47.37% | 40.32 | 1.16 | 31.75 | -24.54 |
| session_extreme_retest_v0 | Evening 16:00-19:59 | 5 | 0 | 2 | 3 | 40.00% | 10.31 | 1.19 | 32.33 | -18.11 |
| breakout_retest | Morning 06:00-11:59 | 5 | 0 | 2 | 3 | 40.00% | -1.21 | 0.96 | 14.46 | -10.05 |
| session_extreme_retest_v0 | Afternoon 12:00-15:59 | 15 | 0 | 5 | 10 | 33.33% | -17.62 | 0.83 | 16.98 | -10.25 |
| session_extreme_retest_v0 | Night 20:00-05:59 | 11 | 0 | 3 | 8 | 27.27% | -59.16 | 0.51 | 20.39 | -15.04 |
| symbol_normalized_round_retest_v0 | Afternoon 12:00-15:59 | 3 | 0 | 0 | 3 | 0.00% | -67.83 | 0.00 | n/a | -22.61 |
| breakout_retest | Afternoon 12:00-15:59 | 11 | 1 | 3 | 8 | 27.27% | -71.63 | 0.34 | 12.24 | -13.54 |
| symbol_normalized_round_retest_v0 | Evening 16:00-19:59 | 6 | 1 | 2 | 4 | 33.33% | -74.99 | 0.40 | 24.58 | -31.04 |
| symbol_normalized_round_retest_v0 | Morning 06:00-11:59 | 18 | 1 | 5 | 13 | 27.78% | -208.29 | 0.35 | 22.65 | -24.74 |

## Worst EA x Symbol x Time Clusters

| candidate | symbol | time_bucket | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| symbol_normalized_round_retest_v0 | XAUUSD | Morning 06:00-11:59 | 17 | 1 | 4 | 13 | 23.53% | -213.80 | 0.34 | 26.94 | -24.74 |
| symbol_normalized_round_retest_v0 | XAUUSD | Evening 16:00-19:59 | 5 | 0 | 1 | 4 | 20.00% | -80.50 | 0.35 | 43.65 | -31.04 |
| symbol_normalized_round_retest_v0 | XAUUSD | Afternoon 12:00-15:59 | 3 | 0 | 0 | 3 | 0.00% | -67.83 | 0.00 | n/a | -22.61 |
| breakout_retest | XAUUSD | Afternoon 12:00-15:59 | 6 | 0 | 1 | 5 | 16.67% | -67.67 | 0.31 | 29.74 | -19.48 |
| session_extreme_retest_v0 | XAUUSD | Night 20:00-05:59 | 7 | 0 | 1 | 6 | 14.29% | -64.71 | 0.44 | 50.19 | -19.15 |
| session_extreme_retest_v0 | XAUUSD | Afternoon 12:00-15:59 | 10 | 0 | 3 | 7 | 30.00% | -16.88 | 0.82 | 25.89 | -13.51 |
| breakout_retest | EURUSD | Afternoon 12:00-15:59 | 4 | 0 | 1 | 3 | 25.00% | -5.43 | 0.50 | 5.51 | -3.65 |
| breakout_retest | EURUSD | Night 20:00-05:59 | 6 | 0 | 2 | 4 | 33.33% | -4.52 | 0.71 | 5.51 | -3.88 |
| session_extreme_retest_v0 | EURUSD | Evening 16:00-19:59 | 1 | 0 | 0 | 1 | 0.00% | -3.64 | 0.00 | n/a | -3.64 |
| breakout_retest | USDJPY | Morning 06:00-11:59 | 1 | 0 | 0 | 1 | 0.00% | -3.50 | 0.00 | n/a | -3.50 |
| session_extreme_retest_v0 | USDJPY | Afternoon 12:00-15:59 | 3 | 0 | 1 | 2 | 33.33% | -2.58 | 0.40 | 1.72 | -2.15 |
| swing_breakout_retest_v0 | USDJPY | Evening 16:00-19:59 | 1 | 0 | 0 | 1 | 0.00% | -1.97 | 0.00 | n/a | -1.97 |

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
| 2026-06-04 08:20:00 | 2026-06-04 10:47:22 | symbol_normalized_round_retest_v0 | XAUUSD | BUY | Morning 06:00-11:59 | -29.80 | kept | [sl 4464.18] |
| 2026-06-04 02:20:00 | 2026-06-04 02:27:26 | breakout_retest | XAUUSD | SELL | Night 20:00-05:59 | -28.07 | kept | [sl 4434.52] |
| 2026-06-04 06:50:00 | 2026-06-04 07:40:33 | symbol_normalized_round_retest_v0 | XAUUSD | BUY | Morning 06:00-11:59 | -27.67 | kept | [sl 4463.32] |
| 2026-06-03 18:20:00 | 2026-06-03 18:49:19 | session_extreme_retest_v0 | XAUUSD | SELL | Evening 16:00-19:59 | -27.41 | unique | [sl 4455.02] |
| 2026-06-04 04:15:01 | 2026-06-04 05:10:02 | symbol_normalized_round_retest_v0 | XAUUSD | SELL | Night 20:00-05:59 | -26.68 | kept | [sl 4460.32] |
| 2026-06-03 06:25:01 | 2026-06-03 08:39:18 | symbol_normalized_round_retest_v0 | XAUUSD | BUY | Morning 06:00-11:59 | -26.56 | kept | [sl 4471.07] |
| 2026-06-01 15:10:00 | 2026-06-01 16:22:00 | symbol_normalized_round_retest_v0 | XAUUSD | BUY | Afternoon 12:00-15:59 | -25.28 | kept | [sl 4498.90] |
| 2026-06-01 20:15:00 | 2026-06-01 20:50:13 | symbol_normalized_round_retest_v0 | XAUUSD | SELL | Night 20:00-05:59 | -25.24 | kept | [sl 4473.46] |

## Interpretation

The loss pattern is mostly a filtering problem, not a broker-cost-only problem. The same strategies perform very differently by time bucket and symbol. Evening/night XAUUSD has been profitable, while morning/afternoon XAUUSD has been the main drag. This report now includes a shadow-only policy so the weak clusters can be measured without changing the running EAs.

Recommended operating stance: keep execution unchanged for the planned observation window, but review the shadow filter delta daily. Do not enforce it until it survives a larger sample.
