# A3 ML Six-Iteration Campaign V1 Final Result

## Final classification

`SIX_ITERATION_RESEARCH_COMPLETE_NO_DEPLOYABLE_SYSTEM`

All six planned iterations were completed. The campaign preserved a profitable historical R1/R2 foundation but did not discover a new high-frequency specialist or an ML policy that passed the frozen gates. Demo and live trading remain unauthorized.

## What each iteration established

1. Data foundation: passed. Official rates, broad-dollar, and CFTC Gold positioning were archived and causally joined to 424,942 Dukascopy M5 rows with zero future-visible joins.
2. Macro repricing: failed. None of the real-yield, yield/USD, or inflation-repricing families passed the train gate.
3. CFTC positioning: failed. None of the managed-money trend, crowded reversal, or producer-confirmation families passed the train gate.
4. Shared account: failed. R1/R2 reached 14 simultaneous same-direction trades and 0.14 lots; the $1,000 risk controls halted after 48 accepted trades.
5. ML ranking: failed. Development AUC was 0.5155 and Spearman was 0.0298. No selection policy passed; later outcomes remained closed.
6. Final qualification: failed. Frequency, Monte Carlo risk at $1,000, new-specialist, ML, shared-account, and untouched-holdout gates failed.

## Historical R1/R2 P&L

Fixed 0.01 lots, hypothetical exact-MT5 history:

| Window | Trades | Net USD | Stress net USD | PF | Stress PF | Closed DD USD |
|---|---:|---:|---:|---:|---:|---:|
| 3 months | 11 | 139.13 | 135.83 | 2.493 | 2.434 | 77.51 |
| 6 months | 20 | 2,812.28 | 2,806.28 | 31.175 | 30.633 | 77.51 |
| 5 years | 497 | 10,975.60 | 10,826.50 | 3.014 | 2.958 | 868.47 |
| 10 years | 1,056 | 12,840.29 | 12,523.49 | 2.433 | 2.369 | 868.47 |

These figures are historical backtest outcomes, not expected future P&L.

## Drawdown and frequency

- Frequency: 0.419 trades per assumed 252-day trading year.
- Largest component MT5 equity drawdown: $1,733.37.
- Conservative component-sum upper boundary: $2,003.38.
- Minimum equity for that upper boundary to equal 15%: approximately $13,355.87.
- Nonnegative six-month blocks: 14/20, or 70%.
- Positive active trading days: 45.89%.

Exact shared-account mark-to-market equity drawdown remains unavailable because the source ledgers do not contain synchronized intratrade equity paths.

## Monte Carlo block bootstrap

Ten thousand 20-trading-day block-bootstrap paths over a ten-year length:

| Starting capital | Ruin probability | Probability DD >= 15% | Median max DD | P95 max DD |
|---:|---:|---:|---:|---:|
| $1,000.00 | 2.22% | 87.65% | 30.17% | 80.87% |
| $13,355.87 | 0.00% | 0.30% | 5.61% | 9.82% |

The larger-capital scenario passing risk simulation does not make the system deployable; frequency, untouched-holdout, shared-account, and new-edge gates still fail.

## Honest conclusion

We have one profitable but low-frequency historical foundation. We do not yet have the requested high-frequency, multi-regime, ML-assisted system. The new daily/weekly external inputs did not create direct entry edge, and the ranker did not rescue negative candidates.

The next research campaign should not retune these failed thresholds. It needs materially new information, most defensibly licensed intraday COMEX trades/depth and point-in-time macro consensus surprises, followed by a new preregistration and untouched chronological holdout.

Python prediction demo, EA signal consumption, demo trading, and live trading are not authorized.
