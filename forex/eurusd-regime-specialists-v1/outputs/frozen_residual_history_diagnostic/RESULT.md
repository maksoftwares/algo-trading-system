# Frozen residual specialist historical diagnostic

Status: **HISTORICAL_FALSIFICATION_FAILED**

This is one exact post-freeze falsification replay. No parameter,
clock, side rule, stop, target, regime, or threshold was searched.
It cannot count as forward evidence or authorize an order.

## Standalone residual result

| Metric | Result |
|---|---:|
| Complete weekdays | 2,608 |
| Eligible trades | 136 |
| Trades/weekday | 0.0521 |
| Weekday coverage | 5.21% |
| Win rate | 42.65% |
| Payoff | 1.4191065417158735 |
| PF | 1.0552 |
| Stressed PF | 0.9398 |
| Net R | 3.9250 |

## Protected M15 plus residual, two-year broker window

| Metric | Full | Second 12 months |
|---|---:|---:|
| Trades | 109 | 61 |
| Trades/weekday | 0.2088 | 0.2337 |
| Weekday coverage | 19.35% | 21.46% |
| Win rate | 49.54% | 49.18% |
| Payoff | 1.441264124865901 | 1.5027888135857286 |
| PF | 1.4151 | 1.4543 |
| Stressed PF | 1.3443 | 1.3833 |
| Best-5%-removed PF | 1.1129 | 1.0977 |
| Net P&L | $62.62 | $38.88 |

Failed frozen portfolio gates:

- `minimum_trades_per_weekday`
- `minimum_weekday_coverage`
- `zero_missing_residual_context`
- `zero_missing_residual_outcome_paths`

Demo-order authorization: `false`.
