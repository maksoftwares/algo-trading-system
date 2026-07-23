# EURUSD Completed-Window Performance

Basis: actual MT5 deal ledger, fixed `0.01` lot, USD 1,000 tester deposit.
Windows end on `2026-06-30`; incomplete July is excluded. Net P&L includes
price profit, swap, and commission.

| Window | Trades | Wins / Losses | Win rate | Net P&L | PF | Max closed DD |
|---|---:|---:|---:|---:|---:|---:|
| 3 months | 68 | 38 / 30 | 55.88% | $3.29 | 1.1010 | $7.19 |
| 6 months | 140 | 80 / 60 | 57.14% | $11.43 | 1.1502 | $8.84 |
| 1 year | 241 | 138 / 103 | 57.26% | $16.03 | 1.1194 | $12.30 |

| Metric | 3 months | 6 months | 1 year |
|---|---:|---:|---:|
| Gross profit | $35.85 | $87.53 | $150.27 |
| Gross loss | -$32.56 | -$76.10 | -$134.24 |
| Swap | $-0.77 | $-1.32 | $-1.98 |
| Average trade | $0.05 | $0.08 | $0.07 |
| Average win | $0.94 | $1.09 | $1.09 |
| Average loss | $-1.09 | $-1.27 | $-1.30 |
| Realized win/loss | 0.8692 | 0.8626 | 0.8355 |
| Best trade | $1.59 | $2.47 | $2.47 |
| Worst trade | $-2.82 | $-2.93 | $-2.93 |
| Positive months | 2/3 | 5/6 | 9/12 |

## Read

The strategy remains profitable in all three windows, but the edge is thin:
PF is `1.1010`, `1.1502`, and `1.1194`. The recent three-month result is only
USD `3.29`. Any improvement study must be preregistered and must not mine a new
set of hours or thresholds from these development outcomes.
