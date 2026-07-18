# Five-Specialist Window Performance V1

Evidence cutoff: `2026-07-01T00:00:00Z` (exclusive).
Realized trades are assigned by exit time.

## Individual results

| Window | Specialist | Trades | Win % | Net USD | PF | Closed DD USD | Net stress R |
|---|---|---:|---:|---:|---:|---:|---:|
| 3M | R1_UPTREND | 0 | 0.00 | 0.00 | 0.000 | 0.00 | N/A |
| 3M | R2_DOWNTREND | 2 | 50.00 | 149.29 | 4.177 | 46.99 | 5.071 |
| 3M | R3_COMPRESSION | 2 | 50.00 | 20.22 | 1.721 | 28.05 | 1.284 |
| 3M | R4_CHOP | 0 | 0.00 | 0.00 | 0.000 | 0.00 | N/A |
| 3M | R5_TRANSITION | 2 | 100.00 | 23.08 | Inf | 0.00 | 1.021 |
| 6M | R1_UPTREND | 25 | 52.00 | 2634.90 | 18.264 | 60.18 | N/A |
| 6M | R2_DOWNTREND | 3 | 66.67 | 536.76 | 12.422 | 46.99 | 19.888 |
| 6M | R3_COMPRESSION | 4 | 50.00 | 87.52 | 2.310 | 38.74 | 4.337 |
| 6M | R4_CHOP | 1 | 0.00 | -1.36 | 0.000 | 1.36 | -0.051 |
| 6M | R5_TRANSITION | 4 | 75.00 | 45.07 | 4.563 | 12.65 | 2.539 |
| 1Y | R1_UPTREND | 116 | 53.45 | 3777.53 | 3.409 | 889.69 | N/A |
| 1Y | R2_DOWNTREND | 4 | 75.00 | 557.87 | 12.871 | 46.99 | 21.726 |
| 1Y | R3_COMPRESSION | 12 | 41.67 | 80.31 | 1.751 | 38.74 | 2.769 |
| 1Y | R4_CHOP | 10 | 40.00 | 30.23 | 1.544 | 17.17 | 2.158 |
| 1Y | R5_TRANSITION | 18 | 55.56 | 62.84 | 2.992 | 12.65 | 3.165 |
| 2Y | R1_UPTREND | 335 | 48.06 | 6524.03 | 2.682 | 889.69 | N/A |
| 2Y | R2_DOWNTREND | 9 | 44.44 | 555.58 | 6.955 | 46.99 | 20.994 |
| 2Y | R3_COMPRESSION | 14 | 42.86 | 103.30 | 1.948 | 38.74 | 6.099 |
| 2Y | R4_CHOP | 21 | 42.86 | 60.53 | 1.612 | 23.52 | 4.881 |
| 2Y | R5_TRANSITION | 60 | 41.67 | 89.11 | 1.790 | 39.32 | 4.696 |

## Additive combined results

| Window | Trades | Active specialists | Win % | Net USD | PF | Closed DD USD | Max concurrent | Max lots | Cross-specialist overlap entries |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 3M | 6 | 3 | 66.67 | 192.59 | 3.566 | 46.99 | 1 | 0.01 | 0 |
| 6M | 37 | 5 | 54.05 | 3302.88 | 12.778 | 57.46 | 10 | 0.10 | 2 |
| 1Y | 160 | 5 | 52.50 | 4508.78 | 3.492 | 889.69 | 12 | 0.12 | 20 |
| 2Y | 439 | 5 | 46.70 | 7332.55 | 2.708 | 889.69 | 14 | 0.14 | 59 |

## Accounting notes

- R1 is exact MT5 closed P&L at 0.01 lot.
- R2-R5 are conservative Dukascopy raw-tick stress-dollar equivalents at 0.01 lot.
- Combined results add every specialist trade and allow simultaneous positions.
- Closed drawdown is based on realized exits, not floating account equity.
- No shared margin, exposure, daily-loss, or liquidation engine is applied.
- Net stress R is not reported for R1 because its frozen ledger does not contain a per-trade initial-risk field.
- These are historical development results and do not authorize training or trading.
