# EURUSD Regime 1 Macro-Pressure Reversal Result

Status: `REJECTED_NO_REGIME_1_HISTORICAL_QUALIFIER`

## Outcome

The original all-regime macro reversal retained a positive aggregate edge under exact ten-year bid/ask execution, but it failed chronological and recent validation. Its predeclared Regime 1 / neutral ownership subset lost money and is rejected.

| Scope | Trades | Win rate | Payoff | PF | Stressed PF | Net R | Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| All-regime replication | 57 | 54.39% | 1.130 | 1.348 | 1.313 | +8.52 | 5.01R |
| Regime 1: chop + compression | 18 | 50.00% | 0.907 | 0.907 | 0.885 | -0.84 | 2.77R |

The all-regime replication passed aggregate PF, stressed PF, win rate, positive-active-month, winner-concentration, and drawdown gates. It failed minimum sample, requested payoff, early-block profitability, and both latest-12-month gates.

## Chronology

| Window | All trades | All PF | All net R | Regime 1 trades | Regime 1 PF | Regime 1 net R |
|---|---:|---:|---:|---:|---:|---:|
| 2017-2019 | 6 | 0.576 | -1.70 | 1 | infinite | +1.06 |
| 2020-2022 H1 | 15 | 1.847 | +4.60 | 5 | 0.735 | -0.80 |
| 2022 H2-2024 H1 | 22 | 1.511 | +4.61 | 10 | 1.224 | +0.90 |
| 2024 H2-2026 H1 | 14 | 1.168 | +1.01 | 2 | 0.000 | -2.01 |
| Latest 12 months | 6 | 0.644 | -1.07 | 2 | 0.000 | -2.01 |
| Latest 6 months | 5 | 0.412 | -1.78 | 2 | 0.000 | -2.01 |

## Frozen Regime Attribution

| Signal regime | Trades | Win rate | Payoff | PF | Net R |
|---|---:|---:|---:|---:|---:|
| Chop | 17 | 52.94% | 0.907 | 1.021 | +0.17 |
| Compression | 1 | 0.00% | 0.000 | 0.000 | -1.01 |
| Trend up | 10 | 50.00% | 1.135 | 1.135 | +0.68 |
| Trend down | 23 | 65.22% | 1.544 | 2.896 | +12.24 |
| Transition | 6 | 50.00% | 1.245 | 1.245 | +0.74 |
| Unsafe | 5 | 60.00% | 0.566 | 0.849 | -0.30 |

The trend-down slice is attractive only after viewing this result. The preregistration prohibits selecting it, so it is diagnostic evidence for a future independently defined regime—not a promoted strategy.

## Decision

Do not use this rule as Regime 1. Retain the all-regime result only as evidence that the macro-pressure mechanism is worth reconsidering later for a separately preregistered trend regime. No broker or demo action is authorized.
