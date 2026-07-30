# Online dense residual regime router

Status: **HISTORICAL_VALIDATION_REJECTED**

The router used only completed prior outcomes in the same causal
regime. The current outcome entered history after selection.
This is retrospective research and cannot authorize an order.

## Locked residual validation

| Metric | Result |
|---|---:|
| Trades | 821 |
| Trades/weekday | 0.7005 |
| Weekday coverage | 70.05% |
| Win rate | 38.37% |
| Payoff | 1.2270528819174527 |
| PF | 0.7669 |
| Stressed PF | 0.6790 |
| Best-5%-removed PF | 0.6334 |

## Protected M15 plus online residual

| Metric | Two years | Latest 12 months |
|---|---:|---:|
| Trades | 430 | 219 |
| Trades/weekday | 0.8238 | 0.8391 |
| Weekday coverage | 80.84% | 81.99% |
| Win rate | 41.63% | 42.47% |
| Payoff | 1.523235585055405 | 1.588556126084045 |
| PF | 1.0906 | 1.1725 |
| Stressed PF | 1.0055 | 1.0860 |
| Net P&L | $26.92 | $27.18 |

Failed gates:

- `minimum_residual_profit_factor`
- `minimum_residual_stressed_profit_factor`
- `minimum_residual_best_removed_profit_factor`
- `minimum_each_residual_half_profit_factor`
- `minimum_combined_trades_per_weekday`
- `minimum_combined_win_rate`
- `minimum_combined_profit_factor`
- `minimum_combined_stressed_profit_factor`
- `minimum_combined_best_removed_profit_factor`
- `minimum_latest_12_month_best_removed_profit_factor`

Forward-evidence credit: `false`.

Demo-order authorization: `false`.
