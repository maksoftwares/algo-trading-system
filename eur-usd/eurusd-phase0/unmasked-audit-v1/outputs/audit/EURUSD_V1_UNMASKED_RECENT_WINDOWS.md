# EURUSD V1 Unmasked Recent-Window Analysis

This is retrospective MT5 Strategy Tester evidence, not live-account profit.
The test endpoint is `2026-07-02` exclusive; the final realized trade exits
on `2026-07-01`. Trades are assigned to windows by exit timestamp.

The account starts at USD 1,000 and every position uses 0.01 lot.

| Period | Trades | W / L | Win rate | Net USD | Return | PF | Avg/trade | Closed-trade DD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 3 months | 89 | 50 / 39 | 56.18% | +6.00 | +0.60% | 1.149 | +0.0674 | 6.75 |
| 6 months | 180 | 102 / 78 | 56.67% | +11.92 | +1.19% | 1.125 | +0.0662 | 10.44 |
| 1 year | 312 | 172 / 140 | 55.13% | +2.98 | +0.30% | 1.017 | +0.0096 | 19.42 |

## Payoff geometry

| Period | Avg win | Avg loss | Payoff ratio | Break-even WR | Actual WR |
|---|---:|---:|---:|---:|---:|
| 3 months | 0.9248 | -1.0318 | 0.8963 | 52.73% | 56.18% |
| 6 months | 1.0512 | -1.2218 | 0.8604 | 53.75% | 56.67% |
| 1 year | 1.0523 | -1.2716 | 0.8276 | 54.72% | 55.13% |

## Cost stress

Primary stress adds 0.5 pip round-trip adverse execution and multiplies
negative commission/swap by 1.25. Severe stress adds 1.0 pip with the
same negative-cost multiplier.

| Period | Primary net | Primary PF | Severe net | Severe PF |
|---|---:|---:|---:|---:|
| 3 months | +1.36 | 1.032 | -3.09 | 0.930 |
| 6 months | +2.59 | 1.026 | -6.41 | 0.938 |
| 1 year | -13.14 | 0.929 | -28.74 | 0.851 |

## Interpretation boundary

The one-year base PF is only 1.0167 and its average trade is USD 0.0096.
Primary cost stress makes the one-year result negative. Recent positive
three- and six-month totals therefore do not establish a robust edge.

`closed_trade_max_drawdown_usd` is reconstructed from realized trade
outcomes with each window rebased to zero. It is not MT5 intratrade or
floating-equity drawdown.
