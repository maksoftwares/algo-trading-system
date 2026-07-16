# XAUUSD Regime Period and Performance Report

Trade attribution uses the strictly prior completed D1 regime at entry. Results are exact-MT5 historical fixed 0.01-lot outcomes, not forecasts.

## Performance by Regime

| Regime | Days | Share | Trades | Win rate | Stress net | Stress PF | Avg/trade | Closed DD | R1 net | R2 net |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| uptrend | 899 | 28.96% | 212 | 56.13% | $9509.09 | 3.149 | $44.85 | $868.47 | $9509.09 | $0.00 |
| downtrend | 278 | 8.96% | 261 | 40.23% | $401.62 | 1.357 | $1.54 | $210.25 | $0.00 | $401.62 |
| chop | 870 | 28.03% | 229 | 32.75% | $685.24 | 1.502 | $2.99 | $208.59 | $960.21 | $-274.97 |
| compression | 494 | 15.91% | 247 | 45.75% | $1800.08 | 2.262 | $7.29 | $332.66 | $1422.88 | $377.20 |
| shock | 249 | 8.02% | 4 | 75.00% | $30.42 | 8.091 | $7.60 | $4.29 | $0.00 | $30.42 |
| transition | 274 | 8.83% | 101 | 34.65% | $130.41 | 1.170 | $1.29 | $260.35 | $45.91 | $84.50 |
| unknown | 40 | 1.29% | 2 | 0.00% | $-33.37 | 0.000 | $-16.68 | $33.37 | $-33.37 | $0.00 |

## Major Regime Episodes

| Period | Episode | Dominant regime | Gold return | Trades | Stress net | Stress PF | Win rate |
|---|---|---|---:|---:|---:|---:|---:|
| 2016-07-09 to 2016-09-30 | post-spike compression / range | compression | -3.14% | 5 | $-44.78 | 0.000 | 0.00% |
| 2016-10-01 to 2016-12-31 | downtrend selloff | downtrend | -12.45% | 78 | $-20.03 | 0.939 | 35.90% |
| 2017-01-01 to 2018-05-31 | broad chop with short trend bursts | chop | 13.19% | 135 | $-79.91 | 0.927 | 31.11% |
| 2018-06-01 to 2018-09-30 | compression into downtrend | downtrend | -8.30% | 91 | $178.67 | 1.848 | 46.15% |
| 2018-10-01 to 2019-05-31 | base-building chop | chop | 8.37% | 76 | $106.18 | 1.228 | 32.89% |
| 2019-06-01 to 2020-09-30 | major bull expansion with shock bursts | uptrend | 45.34% | 70 | $1757.17 | 5.089 | 61.43% |
| 2020-10-01 to 2021-03-31 | post-bull correction / chop-to-downtrend | chop | -10.71% | 75 | $44.68 | 1.081 | 40.00% |
| 2021-04-01 to 2022-01-31 | compression and range rotation | compression | 4.67% | 85 | $-610.02 | 0.421 | 22.35% |
| 2022-02-01 to 2022-03-31 | upside event shock | shock | 7.64% | 3 | $103.55 | 4.848 | 66.67% |
| 2022-04-01 to 2022-10-31 | Fed/USD downtrend | downtrend | -15.21% | 134 | $429.73 | 1.724 | 44.78% |
| 2022-11-01 to 2023-05-31 | recovery uptrend with shock rally | uptrend | 19.87% | 42 | $587.72 | 1.999 | 45.24% |
| 2023-06-01 to 2023-10-31 | compression then violent reversal | compression | 1.49% | 94 | $98.89 | 1.252 | 39.36% |
| 2023-11-01 to 2024-05-31 | fresh bull breakout / high-vol uptrend | uptrend | 18.39% | 21 | $1014.97 | 6.107 | 76.19% |
| 2024-06-01 to 2024-12-31 | bull trend with mid-year chop and year-end pause | uptrend | 12.04% | 47 | $830.38 | 1.867 | 40.43% |
| 2025-01-01 to 2026-02-28 | extreme bull expansion / crowded upside | uptrend | 101.15% | 89 | $7990.46 | 4.783 | 69.66% |
| 2026-03-01 to 2026-07-09 | bull break into chop/downtrend | transition | -23.81% | 11 | $135.83 | 2.434 | 54.55% |

## Interpretation

- Uptrend entries generated most portfolio profit. This confirms that R1 is the main historical engine.
- Downtrend results were positive but substantially weaker; R2 adds coverage, not comparable profitability.
- Chop, compression, and transition attribution reflects R1/R2 trades under a different D1 classifier. It does not prove separate R3/R4 edges.
- Shock performance is based on too few trades to interpret.
