# Passive Paper Observer Spec

Status: ACTIVE SPEC

The passive paper observer collects real-time signal and cost telemetry without broker-side execution.

## Allowed

- Read market data.
- Read spread and symbol metadata.
- Observe would-signals.
- Calculate projected entry, stop, target, stop distance, and estimated cost_R.
- Log whether a would-signal is cost-feasible.

## Forbidden

- `OrderSend`
- `OrderSendAsync`
- `CTrade`
- `trade.Buy`
- `trade.Sell`
- `PositionOpen`
- `PositionModify`
- `PositionClose`

## Log Schema

Create `outputs/paper_observer/passive_cost_observer_log.csv` with:

```text
timestamp_utc
timestamp_broker
symbol
candidate
candidate_family
candidate_status
would_signal
signal_direction
signal_stage
intended_entry_price
intended_stop_loss
intended_take_profit
stop_distance_points
stop_distance_price
bid
ask
spread_points
spread_price
point_size
digits
estimated_entry_spread_R
estimated_slippage_R
estimated_total_cost_R
estimated_gross_edge_R
estimated_net_edge_R
cost_gate_status
session_label
hour_utc
is_rollover_window
tick_fresh
seconds_since_tick
server_time_status
reason_blocked
```

## Cost Gate Labels

| Label | Rule |
| --- | --- |
| COST_OK_STRONG | estimated_total_cost_R <= 0.15 |
| COST_OK_ACCEPTABLE | estimated_total_cost_R <= 0.20 |
| COST_WARN | estimated_total_cost_R <= 0.30 |
| COST_BLOCK | estimated_total_cost_R > 0.30 |

Observer output can inform new hypotheses. It cannot make a cost-suspended candidate execution-eligible.
