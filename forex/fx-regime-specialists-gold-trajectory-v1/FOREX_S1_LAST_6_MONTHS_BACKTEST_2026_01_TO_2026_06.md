# S1 Last Six Completed Months Backtest — January to June 2026

Status: `DEVELOPMENT_EVIDENCE_NOT_UNTOUCHED_CONFIRMATION`

This is the requested historical backtest. These months were already inside the adaptive-exam archive and are not untouched confirmation.

## Summary

- Trades: 6
- PF: 1.2156
- Net: 0.5308R
- Illustrative 0.01-lot P/L: $-1.39
- Expectancy: 0.0885R/trade
- Win rate: 50.00%
- Maximum drawdown: 1.0046R
- Extra 0.5-pip stress: 0.4587R
- After removing the largest winner: -0.4669R
- Active FX days: 155
- Trades per active FX day: 0.0387

## Monthly

| Month | Trades | PF | Net R | Win rate | Max DD R | 0.01-lot USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-01 | 1 | 0.0000 | -1.0012 | 0.00% | 1.0012 | $-5.61 |
| 2026-02 | 1 | Infinity | 0.9977 | 100.00% | 0.0000 | $2.81 |
| 2026-03 | 3 | 4.3739 | 1.5388 | 66.67% | 0.4561 | $2.79 |
| 2026-04 | 1 | 0.0000 | -1.0046 | 0.00% | 1.0046 | $-1.38 |
| 2026-05 | 0 | 0.0000 | 0.0000 | 0.00% | 0.0000 | $0.00 |
| 2026-06 | 0 | 0.0000 | 0.0000 | 0.00% | 0.0000 | $0.00 |

## Direction

| Side | Trades | PF | Net R |
| --- | ---: | ---: | ---: |
| LONG | 4 | 1.3657 | 0.5342 |
| SHORT | 2 | 0.9966 | -0.0034 |

## Exit Reasons

| Exit | Trades | Net R |
| --- | ---: | ---: |
| NEXT_CYCLE | 1 | -0.4561 |
| STOP | 2 | -2.0057 |
| TARGET | 3 | 2.9926 |

Execution uses next-M5 bid/ask prices, embedded spread, 0.1 pip adverse slippage per side, and stop-first resolution on ambiguous bars.
The positive normalized result is concentrated: removing the largest winner leaves the six-month slice negative.

The complete ledger is stored at `outputs/s1_cycle_exit/LAST_6_MONTHS_TRADE_LEDGER.csv`.
