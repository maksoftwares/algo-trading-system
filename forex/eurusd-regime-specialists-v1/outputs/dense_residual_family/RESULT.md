# Preregistered dense residual family

Status: **HISTORICAL_VALIDATION_REJECTED**

Development selected one deterministic rule per causal regime.
Locked validation did not participate in selection. This remains
retrospective research and cannot authorize a demo order.

## Selected regime experts

- `CROSSPAIR_COMPRESSION`: `CASH`
- `BROAD_EUR_UP`: `STRENGTH_60_FADE`
- `BROAD_EUR_DOWN`: `STRENGTH_240_FADE`
- `SHORT_LONG_DISAGREEMENT`: `CASH`
- `MIXED_TRANSITION`: `CASH`

## Locked residual validation

| Metric | Result |
|---|---:|
| Trades | 140 |
| Trades/weekday | 0.1195 |
| Win rate | 36.43% |
| Payoff | 1.356127306550151 |
| PF | 0.7771 |
| Stressed PF | 0.6941 |
| Best-5%-removed PF | 0.6544 |

## Protected M15 plus dense residual

| Metric | Two years | Latest 12 months |
|---|---:|---:|
| Trades | 150 | 79 |
| Trades/weekday | 0.2874 | 0.3027 |
| Weekday coverage | 27.20% | 28.35% |
| Win rate | 46.00% | 45.57% |
| Payoff | 1.5651717181969216 | 1.6390824418168126 |
| PF | 1.3333 | 1.3723 |
| Stressed PF | 1.2592 | 1.2990 |
| Net P&L | $57.11 | $35.26 |

Failed gates:

- `minimum_residual_trades`
- `minimum_residual_trades_per_weekday`
- `minimum_residual_profit_factor`
- `minimum_residual_stressed_profit_factor`
- `minimum_residual_best_removed_profit_factor`
- `minimum_each_residual_half_profit_factor`
- `minimum_combined_trades_per_weekday`
- `minimum_combined_weekday_coverage`
- `minimum_combined_best_removed_profit_factor`

Forward-evidence credit: `false`.

Demo-order authorization: `false`.
