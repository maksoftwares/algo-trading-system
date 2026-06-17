# Observer Shadow-Policy Scoreboard

Status: `PARTIAL_REVIEW_BARS_SUPPLIED`

This report is analysis-only. It does not touch MT5 runtime, orders, charts, or running EAs.

## Resolution Strength

- Scoreboard mode: `broker_joined_only`
- Replay model: `executor_v2`
- Broker-joined rows: `105`
- M5 replay rows: `1552`
- Unresolved rows: `118`

## Top Groups

| aggregation_level | group | family | symbol | time_bucket | direction | normalized_direction | legacy_shadow_action | proposed_v2_shadow_action | proposed_v2_shadow_reason | trend_veto_action | fixed_shadow_action | signals | broker_join | replay | unresolved | wins | losses | open | flat | closed_win_rate_pct | broker_profit_aed | replay_gross_win_rate_pct | replay_net_win_rate_pct | replay_net_r_sum | avg_cost_r | avg_rr | net_breakeven_wr_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| candidate | symbol_normalized_round_retest_v0 | round | XAUUSD | Night 20:00-05:59 | SHORT | SELL | BLOCK | BLOCK | BLOCK_WEAK_EA_ROUND_RETEST_CLONE_FAMILY |  | BLOCK | 13 | 13 | 0 | 0 | 7 | 6 | 0 | 0 | 53.85 | 186.35 | 0.00 | 0.00 |  |  | 1.5002 |  |
| family | round | round | XAUUSD | Night 20:00-05:59 | SHORT | SELL | BLOCK | BLOCK | BLOCK_WEAK_EA_ROUND_RETEST_CLONE_FAMILY |  | BLOCK | 13 | 13 | 0 | 0 | 7 | 6 | 0 | 0 | 53.85 | 186.35 | 0.00 | 0.00 |  |  | 1.5002 |  |
| candidate | round_number_retest_v0 | round | XAUUSD | Night 20:00-05:59 | SHORT | SELL | KEEP | BLOCK | BLOCK_WEAK_EA_ROUND_RETEST_CLONE_FAMILY |  | BLOCK | 11 | 11 | 0 | 0 | 6 | 5 | 0 | 0 | 54.55 | 157.41 | 0.00 | 0.00 |  |  | 1.5000 |  |
| family | round | round | XAUUSD | Morning 06:00-11:59 | SHORT | SELL | BLOCK | BLOCK | BLOCK_WEAK_EA_ROUND_RETEST_CLONE_FAMILY |  | BLOCK | 11 | 11 | 0 | 0 | 3 | 8 | 0 | 0 | 27.27 | -161.00 | 0.00 | 0.00 |  |  | 1.5000 |  |
| candidate | round_number_retest_v0 | round | XAUUSD | Morning 06:00-11:59 | SHORT | SELL | BLOCK | BLOCK | BLOCK_WEAK_EA_ROUND_RETEST_CLONE_FAMILY |  | BLOCK | 10 | 10 | 0 | 0 | 2 | 8 | 0 | 0 | 20.00 | -206.28 | 0.00 | 0.00 |  |  | 1.5001 |  |
| candidate | symbol_normalized_round_retest_v0 | round | XAUUSD | Morning 06:00-11:59 | SHORT | SELL | BLOCK | BLOCK | BLOCK_WEAK_EA_ROUND_RETEST_CLONE_FAMILY |  | BLOCK | 10 | 10 | 0 | 0 | 3 | 7 | 0 | 0 | 30.00 | -135.02 | 0.00 | 0.00 |  |  | 1.4998 |  |
| candidate | symbol_normalized_round_retest_v0 | round | XAUUSD | Night 20:00-05:59 | LONG | BUY | BLOCK | BLOCK | BLOCK_WEAK_EA_ROUND_RETEST_CLONE_FAMILY |  | BLOCK | 9 | 9 | 0 | 0 | 2 | 7 | 0 | 0 | 22.22 | -41.03 | 0.00 | 0.00 |  |  | 1.5002 |  |
| family | round | round | XAUUSD | Night 20:00-05:59 | LONG | BUY | BLOCK | BLOCK | BLOCK_WEAK_EA_ROUND_RETEST_CLONE_FAMILY |  | BLOCK | 9 | 9 | 0 | 0 | 2 | 7 | 0 | 0 | 22.22 | -41.03 | 0.00 | 0.00 |  |  | 1.5002 |  |
| family | round | round | XAUUSD | Afternoon 12:00-15:59 | SHORT | SELL | BLOCK | BLOCK | BLOCK_WEAK_EA_ROUND_RETEST_CLONE_FAMILY |  | BLOCK | 8 | 8 | 0 | 0 | 0 | 8 | 0 | 0 | 0.00 | -146.75 | 0.00 | 0.00 |  |  | 1.5001 |  |
| candidate | symbol_normalized_round_retest_v0 | round | XAUUSD | Afternoon 12:00-15:59 | SHORT | SELL | BLOCK | BLOCK | BLOCK_WEAK_EA_ROUND_RETEST_CLONE_FAMILY |  | BLOCK | 7 | 7 | 0 | 0 | 0 | 7 | 0 | 0 | 0.00 | -135.47 | 0.00 | 0.00 |  |  | 1.5000 |  |
| candidate | round_number_retest_v0 | round | XAUUSD | Afternoon 12:00-15:59 | SHORT | SELL | BLOCK | BLOCK | BLOCK_WEAK_EA_ROUND_RETEST_CLONE_FAMILY |  | BLOCK | 5 | 5 | 0 | 0 | 0 | 5 | 0 | 0 | 0.00 | -86.65 | 0.00 | 0.00 |  |  | 1.5003 |  |
| candidate | round_number_retest_v0 | round | XAUUSD | Night 20:00-05:59 | LONG | BUY | KEEP | BLOCK | BLOCK_WEAK_EA_ROUND_RETEST_CLONE_FAMILY |  | BLOCK | 5 | 5 | 0 | 0 | 1 | 4 | 0 | 0 | 20.00 | -81.22 | 0.00 | 0.00 |  |  | 1.4999 |  |
| candidate | symbol_normalized_round_retest_v0 | round | XAUUSD | Evening 16:00-19:59 | SHORT | SELL | BLOCK | BLOCK | BLOCK_WEAK_EA_ROUND_RETEST_CLONE_FAMILY |  | BLOCK | 5 | 5 | 0 | 0 | 2 | 3 | 0 | 0 | 40.00 | 91.66 | 0.00 | 0.00 |  |  | 1.4999 |  |
| family | round | round | XAUUSD | Evening 16:00-19:59 | SHORT | SELL | BLOCK | BLOCK | BLOCK_WEAK_EA_ROUND_RETEST_CLONE_FAMILY |  | BLOCK | 5 | 5 | 0 | 0 | 2 | 3 | 0 | 0 | 40.00 | 91.66 | 0.00 | 0.00 |  |  | 1.4999 |  |
| candidate | round_number_retest_v0 | round | XAUUSD | Afternoon 12:00-15:59 | LONG | BUY | BLOCK | BLOCK | BLOCK_WEAK_EA_ROUND_RETEST_CLONE_FAMILY |  | BLOCK | 4 | 4 | 0 | 0 | 0 | 4 | 0 | 0 | 0.00 | -119.45 | 0.00 | 0.00 |  |  | 1.5002 |  |
| candidate | round_number_retest_v0 | round | XAUUSD | Evening 16:00-19:59 | SHORT | SELL | KEEP | BLOCK | BLOCK_WEAK_EA_ROUND_RETEST_CLONE_FAMILY |  | BLOCK | 4 | 4 | 0 | 0 | 2 | 2 | 0 | 0 | 50.00 | 98.87 | 0.00 | 0.00 |  |  | 1.5000 |  |
| candidate | symbol_normalized_round_retest_v0 | round | XAUUSD | Afternoon 12:00-15:59 | LONG | BUY | BLOCK | BLOCK | BLOCK_WEAK_EA_ROUND_RETEST_CLONE_FAMILY |  | BLOCK | 4 | 4 | 0 | 0 | 0 | 4 | 0 | 0 | 0.00 | -119.89 | 0.00 | 0.00 |  |  | 1.5002 |  |
| candidate | symbol_normalized_round_retest_v0 | round | XAUUSD | Morning 06:00-11:59 | LONG | BUY | BLOCK | BLOCK | BLOCK_WEAK_EA_ROUND_RETEST_CLONE_FAMILY |  | BLOCK | 4 | 4 | 0 | 0 | 1 | 3 | 0 | 0 | 25.00 | -39.03 | 0.00 | 0.00 |  |  | 1.5001 |  |
| family | round | round | XAUUSD | Afternoon 12:00-15:59 | LONG | BUY | BLOCK | BLOCK | BLOCK_WEAK_EA_ROUND_RETEST_CLONE_FAMILY |  | BLOCK | 4 | 4 | 0 | 0 | 0 | 4 | 0 | 0 | 0.00 | -119.89 | 0.00 | 0.00 |  |  | 1.5002 |  |
| family | round | round | XAUUSD | Morning 06:00-11:59 | LONG | BUY | BLOCK | BLOCK | BLOCK_WEAK_EA_ROUND_RETEST_CLONE_FAMILY |  | BLOCK | 4 | 4 | 0 | 0 | 1 | 3 | 0 | 0 | 25.00 | -39.03 | 0.00 | 0.00 |  |  | 1.5001 |  |
| candidate | round_number_retest_v0 | round | XAUUSD | Morning 06:00-11:59 | LONG | BUY | BLOCK | BLOCK | BLOCK_WEAK_EA_ROUND_RETEST_CLONE_FAMILY |  | BLOCK | 3 | 3 | 0 | 0 | 1 | 2 | 0 | 0 | 33.33 | -28.85 | 0.00 | 0.00 |  |  | 1.5005 |  |
| candidate | round_number_retest_v0 | round | XAUUSD | Night 20:00-05:59 | LONG | BUY | BLOCK | BLOCK | BLOCK_WEAK_EA_ROUND_RETEST_CLONE_FAMILY |  | BLOCK | 3 | 3 | 0 | 0 | 1 | 2 | 0 | 0 | 33.33 | 65.79 | 0.00 | 0.00 |  |  | 1.5003 |  |
| candidate | round_number_retest_v0 | round | XAUUSD | Night 20:00-05:59 | SHORT | SELL | BLOCK | BLOCK | BLOCK_WEAK_EA_ROUND_RETEST_CLONE_FAMILY |  | BLOCK | 2 | 2 | 0 | 0 | 1 | 1 | 0 | 0 | 50.00 | 25.64 | 0.00 | 0.00 |  |  | 1.5009 |  |
| candidate | symbol_normalized_round_retest_v0 | round | XAUUSD | Evening 16:00-19:59 | LONG | BUY | BLOCK | BLOCK | BLOCK_WEAK_EA_ROUND_RETEST_CLONE_FAMILY |  | BLOCK | 2 | 2 | 0 | 0 | 0 | 2 | 0 | 0 | 0.00 | -39.21 | 0.00 | 0.00 |  |  | 1.4996 |  |
| family | round | round | XAUUSD | Evening 16:00-19:59 | LONG | BUY | BLOCK | BLOCK | BLOCK_WEAK_EA_ROUND_RETEST_CLONE_FAMILY |  | BLOCK | 2 | 2 | 0 | 0 | 0 | 2 | 0 | 0 | 0.00 | -39.21 | 0.00 | 0.00 |  |  | 1.4996 |  |
| candidate | breakout_retest | breakout | EURUSD | Night 20:00-05:59 | SHORT | SELL | KEEP | KEEP | KEEP |  | KEEP | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.00 | 27.86 | 0.00 | 0.00 |  |  | 1.4935 |  |
| candidate | round_number_retest_v0 | round | XAUUSD | Evening 16:00-19:59 | LONG | BUY | BLOCK | BLOCK | BLOCK_WEAK_EA_ROUND_RETEST_CLONE_FAMILY |  | BLOCK | 1 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0.00 | -23.04 | 0.00 | 0.00 |  |  | 1.4996 |  |
| candidate | round_number_retest_v0 | round | XAUUSD | Evening 16:00-19:59 | LONG | BUY | KEEP | BLOCK | BLOCK_WEAK_EA_ROUND_RETEST_CLONE_FAMILY |  | BLOCK | 1 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0.00 | -18.00 | 0.00 | 0.00 |  |  | 1.4996 |  |
| candidate | swing_breakout_retest_v0 | breakout | EURUSD | Night 20:00-05:59 | SHORT | SELL | KEEP | KEEP | KEEP |  | KEEP | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.00 | 27.86 | 0.00 | 0.00 |  |  | 1.4935 |  |
| family | breakout | breakout | EURUSD | Night 20:00-05:59 | SHORT | SELL | KEEP | KEEP | KEEP |  | KEEP | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.00 | 27.86 | 0.00 | 0.00 |  |  | 1.4935 |  |

## Portfolio Rule

Use `aggregation_level=family` rows for portfolio totals. Candidate rows can double-count clone signals.
If replay calibration is quarantined, use scoreboards generated with `scoreboard_mode=broker_joined_only`.
