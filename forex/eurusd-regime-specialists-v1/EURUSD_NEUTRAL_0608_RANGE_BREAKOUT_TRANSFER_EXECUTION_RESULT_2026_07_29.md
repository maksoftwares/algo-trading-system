# EURUSD Neutral 06:00-08:00 UTC range-breakout execution result

Status: `REJECTED_EXACT_TRANSFER_EXECUTION`

## Primary result

| Trades | Wins | Win rate | Realized payoff | PF | Net R | Max drawdown |
|---:|---:|---:|---:|---:|---:|---:|
| 121 | 50 | 41.32% | 0.935 | 0.658 | -20.063 | 20.997R |

The result misses the requested neighborhood of approximately 50% win rate,
1.5 payoff, and a materially profitable PF.

## Chronology

| Window | Trades | Win rate | Payoff | PF | Net R |
|---|---:|---:|---:|---:|---:|
| Development 2019-2022 | 73 | 39.73% | 0.865 | 0.570 | -15.090 |
| OOS 2023 | 6 | 66.67% | 1.468 | 2.936 | +2.478 |
| OOS 2024 | 15 | 46.67% | 0.752 | 0.658 | -2.749 |
| OOS 2025 | 20 | 40.00% | 0.909 | 0.606 | -4.659 |
| OOS 2026 H1 / latest six months | 7 | 28.57% | 2.456 | 0.982 | -0.044 |

The isolated 2023 result cannot be activated because the rule forbids
post-outcome year selection and had only six trades.

## Direction and robustness

| Slice | Trades | Win rate | Payoff | PF | Net R |
|---|---:|---:|---:|---:|---:|
| Long | 63 | 38.10% | 0.895 | 0.551 | -14.507 |
| Short | 58 | 44.83% | 0.972 | 0.789 | -5.556 |
| Extra 0.5-pip stress | 121 | 41.32% | 0.893 | 0.629 | -22.332 |
| Top 5% removed | 114 | 37.72% | 0.792 | 0.480 | -30.537 |

Oracle resemblance was zero exact and zero same-side matches within 15
minutes, using one-to-one matching against 2,615 Neutral oracle rows.

## Routing

- 272 frozen candidates entered the evaluator.
- 121 trades closed.
- 131 candidates were skipped because a prior position remained open.
- 20 candidates lacked an exact complete 12-hour path and routed to cash.
- No parameter, direction, hour, weekday, side, year, or subgroup was changed
  after the result opened.

## Verdict

This exact transferred family is retired. It is not profitable, does not
resemble the Regime 1 oracle, and cannot authorize demo or live trading.
No broker action occurred.
