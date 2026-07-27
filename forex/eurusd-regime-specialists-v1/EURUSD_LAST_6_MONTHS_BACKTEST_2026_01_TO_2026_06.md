# EURUSD last six months backtest

Period: 2026-01-01 through 2026-06-30 UTC

Cost model: observed Dukascopy bid/ask with 0.70-pip minimum retail spread and 0.10-pip adverse slippage per side

Decision: `NO_TRADABLE_PORTFOLIO`

## Governed result

No regime specialist passed the frozen all-window admission rules. Therefore the governed portfolio takes zero trades. This is the correct production-facing result.

## Forced all-owner diagnostic

The table below answers what the high-frequency stream would have done if the rejected owners had nevertheless been traded. It is diagnostic only.

| Metric | Result |
| --- | ---: |
| Trades | 197 |
| Trades per Monday-Friday UTC trading day | 1.527 |
| Profit factor | 0.995 |
| Net | -0.411R |
| Expectancy | -0.0021R/trade |
| Win rate | 55.84% |
| Maximum drawdown | 13.81R |
| Fixed 0.01-lot P&L | +$4.73 |

The negative R result and slightly positive fixed-lot dollars are not contradictory: stop distances vary, so each fixed-lot trade carries a different amount of risk. Admission uses risk-normalized R.

| Month | Trades | PF | Net R | Fixed 0.01-lot P&L |
| --- | ---: | ---: | ---: | ---: |
| 2026-01 | 27 | 1.563 | +5.13 | +$11.75 |
| 2026-02 | 25 | 0.722 | -3.65 | -$6.75 |
| 2026-03 | 40 | 0.866 | -2.56 | -$2.39 |
| 2026-04 | 31 | 0.681 | -5.56 | -$8.16 |
| 2026-05 | 37 | 1.411 | +5.83 | +$7.81 |
| 2026-06 | 37 | 1.024 | +0.39 | +$2.48 |

## Recent specialist attribution

| Specialist | Trades | PF | Net R | Fixed 0.01-lot P&L |
| --- | ---: | ---: | ---: | ---: |
| Compression reversion | 119 | 0.768 | -14.07 | -$12.72 |
| Supportive pullback | 15 | 0.594 | -3.78 | -$5.85 |
| Neutral auction | 53 | 1.497 | +9.53 | +$11.51 |
| Opposing capitulation | 23 | 2.817 | +9.18 | +$12.13 |

Recent neutral/opposing strength cannot be promoted: both specialists fail the longer frozen windows and robustness tests. Selecting them now would be post-outcome regime chasing.
