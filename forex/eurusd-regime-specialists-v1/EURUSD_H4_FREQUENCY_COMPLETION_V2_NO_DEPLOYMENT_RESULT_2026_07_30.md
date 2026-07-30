# EURUSD H4 frequency-completion V2 no-deployment result

Status: **V2_PREDEPLOYMENT_VALIDATION_PASSED_NO_DEPLOYMENT**

The hardened chop-only V2 compiled with zero errors/warnings and passed the
isolated Capital.com broker-transfer, transaction-confirmation,
restart-recovery, cost/outlier, and disarmed fail-closed checks. No file was
installed into a demo terminal and no demo order was authorized.

| Window | Trades | Trades/weekday | Win rate | Payoff | PF | 0.01-lot P&L |
|---|---:|---:|---:|---:|---:|---:|
| Two-year transfer | 313 | 0.600 | 53.04% | 1.324 | 1.495 | $+123.56 |
| First 12 months | 143 | - | 53.85% | 1.152 | 1.344 | $+40.64 |
| Latest 12 months | 170 | 0.651 | 52.35% | 1.483 | 1.629 | $+82.92 |
| Latest 6 months | 88 | - | 53.41% | 1.496 | 1.715 | $+49.70 |

All six chop sleeves traded and every broker trade used exactly 0.01 lot.
The failed compression sleeves placed zero trades. History quality was
98%; maximum balance drawdown was
46.93 (0.46%).

The restart exercise rebuilt state on
126 trading days and exactly replayed the
unchanged 88-trade latest-six-month result, with zero duplicate
sleeve-days. All 313 entry requests were transaction-confirmed.
The disarmed test observed 11 valid signals,
blocked all of them, and placed zero trades.

One-pip-plus-$0.07 stressed PF was
1.256.
Removing the three best months left PF
1.208;
removing the best 5% of active days left PF
1.199.

This validates executable behavior on MT5 history. It is not fresh future
evidence and does not authorize installation or orders.

Failed gates: none.
