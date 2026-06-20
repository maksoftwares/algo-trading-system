# Observer Shadow-Policy Scoreboard

Status: `PARTIAL_REVIEW_NEEDS_FRESH_M5_BARS`

This report is analysis-only. It does not touch MT5 runtime, orders, charts, or running EAs.

## Resolution Strength

- Scoreboard mode: `broker_joined_only`
- Replay model: `executor_v2`
- Broker-joined rows: `2`
- M5 replay rows: `0`
- Unresolved rows: `2641`

## Top Groups

| aggregation_level | group | family | symbol | time_bucket | direction | normalized_direction | legacy_shadow_action | proposed_v2_shadow_action | proposed_v2_shadow_reason | trend_veto_action | fixed_shadow_action | signals | broker_join | replay | unresolved | wins | losses | open | flat | closed_win_rate_pct | broker_profit_aed | replay_gross_win_rate_pct | replay_net_win_rate_pct | replay_net_r_sum | avg_cost_r | avg_rr | net_breakeven_wr_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| candidate | breakout_retest | breakout | XAUUSD | Evening 16:00-19:59 | LONG | BUY | KEEP | KEEP | KEEP |  | KEEP | 2 | 2 | 0 | 0 | 0 | 2 | 0 | 0 | 0.00 | -23.47 | 0.00 | 0.00 |  |  | 1.4992 |  |
| family | breakout | breakout | XAUUSD | Evening 16:00-19:59 | LONG | BUY | KEEP | KEEP | KEEP |  | KEEP | 2 | 2 | 0 | 0 | 0 | 2 | 0 | 0 | 0.00 | -23.47 | 0.00 | 0.00 |  |  | 1.4992 |  |

## Portfolio Rule

Use `aggregation_level=family` rows for portfolio totals. Candidate rows can double-count clone signals.
If replay calibration is quarantined, use scoreboards generated with `scoreboard_mode=broker_joined_only`.
