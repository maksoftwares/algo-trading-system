# RSI chronological regime selector

Status: **HISTORICAL_VALIDATION_REJECTED**

Regimes were admitted using the first 12 months only. The second
12 months were locked validation and did not alter selection.

Selected regimes:

- `NEUTRAL`
- `JOINT_COMPRESSION`
- `SHOCK`

## Locked last-12-month combined result

- RSI trades: `289`
- Protected M15 trades: `61`
- Combined trades: `350`
- Trades/weekday: `1.3410`
- Weekday coverage: `54.02%`
- Win rate: `51.43%`
- Payoff: `0.9509255373711941`
- PF: `1.0069`
- PF after +0.5 pip: `0.9237`
- Best-5%-removed PF: `0.7296`
- Net P&L: `$1.39`

Failed gates:

- `NEUTRAL_minimum_profit_factor`
- `NEUTRAL_minimum_stressed_profit_factor`
- `JOINT_COMPRESSION_minimum_stressed_profit_factor`
- `SHOCK_minimum_profit_factor`
- `SHOCK_minimum_stressed_profit_factor`
- `maximum_trades_per_weekday`
- `minimum_weekday_coverage`
- `minimum_payoff_ratio`
- `minimum_profit_factor`
- `minimum_stressed_profit_factor`
- `minimum_best_removed_profit_factor`
- `maximum_concurrent_positions`
- `maximum_same_entry_overlap_timestamps`

Forward-evidence credit: `false`.

Demo-order authorization: `false`.
