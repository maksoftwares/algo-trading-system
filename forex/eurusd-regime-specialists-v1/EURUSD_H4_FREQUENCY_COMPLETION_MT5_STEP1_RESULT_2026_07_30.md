# EURUSD H4 frequency-completion MT5 step-one result

Status: **MT5_STEP1_VALIDATION_PASSED_NO_DEPLOYMENT**

The 12-sleeve EA compiled with zero errors/warnings and passed the isolated
Capital.com broker-transfer, restart-recovery, and disarmed fail-closed checks.
No file was installed into a demo terminal and no demo order was authorized.

| Window | Trades | Trades/weekday | Win rate | Payoff | PF | 0.01-lot P&L |
|---|---:|---:|---:|---:|---:|---:|
| Two-year transfer | 416 | 0.797 | 48.80% | 1.375 | 1.311 | $+111.71 |
| Latest 12 months | 244 | 0.935 | 50.00% | 1.542 | 1.542 | $+106.42 |
| Latest 6 months | 110 | - | 53.64% | 1.472 | 1.703 | $+57.95 |

Research-window count: 462.
MT5 count: 416
(90.04%).
All 12 frozen sleeves traded. Every broker trade used exactly 0.01 lot.
History quality was 98%; maximum
balance drawdown was 51.26 (0.51%).

The restart exercise rebuilt state on
127 trading days and exactly replayed the
unchanged 110-trade latest-six-month result, with zero duplicate sleeve-days.
The disarmed test observed 21 valid signals,
blocked all of them, and placed zero trades.

This is an aggregate broker transfer, not exact event-by-event replay against
the research M5 ledger. It validates executable behavior on MT5 history; it is
not fresh future evidence and does not authorize deployment.

Failed gates: none.
