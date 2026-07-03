# A1 XAU M5 Momentum Short-Companion Diagnostic

Generated: `2026-07-02`

Status: `DIAGNOSTIC_ONLY_NOT_PROMOTED`

The owner clarified that sparse strategies are not acceptable: the project needs multiple trades per active day, win rate above 50%, and positive expectancy. After the long-side V3 candidate met that shape better than the sparse RR2 lane, this short-side diagnostic tested whether a short-only companion can add daily opportunity count without damaging the book.

Result: the short side is promising in the recent window but not stable enough across the older OOS window. It should not be attached or promoted yet. The long-side V3 candidate remains the clean review target; the short side should stay as a reviewer-visible companion hypothesis.

No live/demo MT5 runtime was changed. All tests used the isolated MT5 Strategy Tester sandbox `C:\MT5A1M5MomentumBacktest`.

## Split Results

| Window | Variant | Trades | WR | Net USD | PF | Active Days | Trades / Active Day | Positive Months | Negative Months | Net After Top 10 Winners Removed |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Older OOS `2022.07-2024.06` | `night_early` | 147 | 57.82% | -17.88 | 0.92 | 99 | 1.48 | 7 | 12 | -44.91 |
| Older OOS `2022.07-2024.06` | `core_1_5_15_19` | 195 | 56.41% | -23.92 | 0.93 | 115 | 1.70 | 11 | 9 | -79.60 |
| Older OOS `2022.07-2024.06` | `broad_positive` | 261 | 54.41% | -69.01 | 0.85 | 131 | 1.99 | 9 | 12 | -124.69 |
| Older OOS `2022.07-2024.06` | `oos_safe` | 82 | 67.07% | +56.99 | 1.41 | 62 | 1.32 | 12 | 6 | -1.51 |
| Recent `2024.07-2026.06` | `night_early` | 81 | 72.84% | +234.66 | 2.21 | 41 | 1.98 | 12 | 4 | +117.89 |
| Recent `2024.07-2026.06` | `core_1_5_15_19` | 105 | 69.52% | +237.19 | 1.86 | 54 | 1.94 | 12 | 4 | +120.42 |
| Recent `2024.07-2026.06` | `broad_positive` | 157 | 68.79% | +325.74 | 1.74 | 65 | 2.42 | 10 | 6 | +204.89 |
| Recent `2024.07-2026.06` | `oos_safe` | 30 | 50.00% | -41.63 | 0.73 | 24 | 1.25 | 5 | 9 | -127.84 |
| Four-year `2022.07-2026.06` | `night_early` | 228 | 63.16% | +216.78 | 1.51 | 140 | 1.63 | 19 | 16 | +100.01 |
| Four-year `2022.07-2026.06` | `core_1_5_15_19` | 300 | 61.00% | +213.27 | 1.35 | 169 | 1.78 | 23 | 13 | +96.50 |
| Four-year `2022.07-2026.06` | `broad_positive` | 418 | 59.81% | +256.73 | 1.29 | 196 | 2.13 | 19 | 18 | +135.88 |
| Four-year `2022.07-2026.06` | `oos_safe` | 112 | 62.50% | +15.36 | 1.05 | 86 | 1.30 | 17 | 15 | -73.68 |

## Combined With Long V3

| Combination | Trades | WR | Net USD | PF | Active Days | Trades / Active Day | Positive Months | Negative Months |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Long V3 only | 925 | 66.81% | +988.26 | 1.53 | 346 | 2.67 | 35 | 12 |
| Long V3 + short `night_early` | 1153 | 66.09% | +1205.04 | 1.53 | 486 | 2.37 | 35 | 13 |
| Long V3 + short `core_1_5_15_19` | 1225 | 65.39% | +1201.53 | 1.48 | 515 | 2.38 | 35 | 13 |
| Long V3 + short `broad_positive` | 1343 | 64.63% | +1244.99 | 1.45 | 542 | 2.48 | 33 | 15 |

## Interpretation

- The short side improves coverage and total net in the full four-year view.
- The short side does not pass clean split discipline because practical variants lost in the older OOS window.
- The only profitable older-OOS short slice is too sparse and loses after removing the top 10 winners.
- The recent short strength may be regime-specific. It should not be attached as a live demo lane until independently reviewed and forward-tested.
- The best current action remains: send the long V3 candidate for review as the primary frequency-first lane. Treat short-side V1 as a companion research note, not a promoted strategy.

## Raw Generated Artifacts

The following generated reports are local outputs and may be ignored by Git:

- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_SHORT_V1_OOS_2022_07_2024_06.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_SHORT_V1_CURRENT_2024_07_2026_06.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_SHORT_V1_FOUR_YEAR_2022_07_2026_06.md`

