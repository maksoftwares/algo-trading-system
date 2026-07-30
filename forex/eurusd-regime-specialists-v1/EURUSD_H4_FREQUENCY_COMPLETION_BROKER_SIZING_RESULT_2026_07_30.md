# EURUSD H4 broker-executable sizing lock

Status: **BROKER_SIZING_AND_RESEARCH_EDGE_LOCKED**

The 2,532 frozen trade identities are unchanged. The earlier 0.015-lot
interpretation is not on Capital.com's observed 0.01 lot grid, so the executable
contract is uniformly reduced to 0.01 lot per trade.

| Window | Trades | Win rate | Payoff | PF | Net R | 0.01-lot P&L |
|---|---:|---:|---:|---:|---:|---:|
| Full 2017-2026 | 2,532 | 47.24% | 1.360 | 1.218 | +27.952 | $+529.34 |
| Recent 2024H2-2026H1 | 462 | 50.22% | 1.385 | 1.397 | +8.587 | $+164.21 |
| Latest 12 months | 266 | 52.63% | 1.435 | 1.594 | +7.130 | $+149.40 |
| Latest 6 months | 111 | 57.66% | 1.357 | 1.848 | +3.781 | $+70.99 |

The frozen grid is minimum 0.01 lot, step 0.01 lot, selected 0.01 lot.
Maximum concurrent exposure is nine positions and 0.90R initial research risk.
Uniform scaling leaves frequency, win rate, payoff, profit factor, signals, and
exits unchanged while reducing cash exposure and drawdown by one third from the
superseded 0.015-lot interpretation.

This locks research sizing only. It does not authorize demo or live orders.
