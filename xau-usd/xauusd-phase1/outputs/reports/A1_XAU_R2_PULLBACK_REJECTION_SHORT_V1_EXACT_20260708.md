# A1 XAU R2 Pullback-Rejection Short V1 Exact-MT5

Generated UTC: `2026-07-08T20:32:21Z`
Status: `R2_PULLBACK_REJECTION_SHORT_V1_SHADOW_ONLY`

## Scope and Runtime Boundary

Exact-MT5 research-only run for a strict Router V1 R2 short specialist. No demo/live runtime, chart, preset, profile, order, position, account, or broker state was changed.

Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_R2_PULLBACK_REJECTION_SHORT_V1_PREREG_2026_07_08.md`
Preregistration SHA256: `d30c883b5c6f0113d7249f1233acf3c8d0f8dfe605c113f468f9d4b19cf9c057`
EA source commit hash: `1c64e99d9582161b69e9efebf4ee45a1fc4d0cdc`
Repo HEAD during run: `1617f85b4655db7c988dd348cb405fcd3805ef8e`
Tester input set SHA256: `7eba00b454f098b39fbc33d92ff08027adc0ca81160d3b6dbda67804e02159cd`
MT5 raw component evidence: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_PULLBACK_REJECTION_SHORT_V1_EXACT_20260708_MT5_COMPONENTS.md`
Compile log: `C:\MT5A1M5MomentumBacktest\Logs\compile_A1XauM5MomentumContinuationExecutor_variants_20260701.log`

## Standalone Results

| Variant | Trades | WR% | W/L | PF | Net | Stress W/L | Stress PF | Stress net | Recent3 trades | Recent3 net | June trades | June net | 2023+2024 net | Max DD | Best month% | Top10 rem | Top3 days rem | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `r2_pullback_short_m15_confirm` | 464 | 34.91 | 2.2386 | 1.2009 | 412.09 | 2.1017 | 1.1274 | 272.89 | 81 | 455.60 | 30 | 419.92 | -90.52 | 427.24 | 101.90 | -0.54 | -116.54 | False |
| `r2_pullback_short_h1_confirm` | 211 | 39.34 | 2.2504 | 1.4592 | 426.88 | 2.1214 | 1.3756 | 363.58 | 11 | 139.13 | 5 | 13.64 | 56.78 | 124.36 | 35.16 | 72.85 | 161.70 | False |

## Combined With Current R1 Book

| Book | Trades | WR% | W/L | PF | Net | Stress W/L | Stress PF | Recent3 trades | Recent3 net | Max DD | Best month% | Dropped | Top10 rem | Top3 days rem | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `current_r1_plus_r2_pullback_short_m15_confirm` | 1022 | 43.25 | 2.9963 | 2.2834 | 9128.45 | 2.9009 | 2.2107 | 81 | 455.60 | 889.69 | 29.52 | 0 | 6219.80 | 6764.15 | False |
| `current_r1_plus_r2_pullback_short_h1_confirm` | 769 | 47.20 | 2.8255 | 2.5263 | 9143.24 | 2.7493 | 2.4581 | 11 | 139.13 | 889.69 | 29.48 | 0 | 6234.59 | 6778.94 | False |

## Current R1 Reference

Current R1 book: 558 trades, WR 50.18%, W/L 2.7028, PF 2.7223, net 8716.36, recent3 trades 0, recent3 net 0.00, max DD 889.69, best-month share 30.92%.

## Router Block Summary

### `r2_pullback_short_m15_confirm`
- `regime_router_block_short_r2_downtrend_only_state_chop`: 1286
- `regime_router_block_short_r2_downtrend_only_state_compression`: 211
- `regime_router_block_short_r2_downtrend_only_state_shock`: 297
- `regime_router_block_short_r2_downtrend_only_state_uptrend`: 30
- `stop_ceiling_exceeded`: 62

### `r2_pullback_short_h1_confirm`
- `regime_router_block_short_r2_downtrend_only_state_chop`: 606
- `regime_router_block_short_r2_downtrend_only_state_compression`: 101
- `regime_router_block_short_r2_downtrend_only_state_shock`: 172
- `regime_router_block_short_r2_downtrend_only_state_uptrend`: 14
- `stop_ceiling_exceeded`: 72

## Yearly Table

| Book | Period | Trades | WR% | W/L | PF | Net |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `r2_pullback_short_m15_confirm` | `2022` | 186 | 36.56 | 1.8619 | 1.0729 | 47.01 |
| `r2_pullback_short_m15_confirm` | `2023` | 181 | 31.49 | 2.1296 | 0.9789 | -13.36 |
| `r2_pullback_short_m15_confirm` | `2024` | 16 | 6.25 | 2.3148 | 0.1543 | -77.16 |
| `r2_pullback_short_m15_confirm` | `2025` | 0 | 0.00 | 0.0000 | 0.0000 | 0.00 |
| `r2_pullback_short_m15_confirm` | `2026` | 81 | 44.44 | 2.0851 | 1.6681 | 455.60 |
| `r2_pullback_short_h1_confirm` | `2022` | 89 | 42.70 | 2.2165 | 1.6515 | 230.97 |
| `r2_pullback_short_h1_confirm` | `2023` | 100 | 37.00 | 2.1721 | 1.2757 | 108.66 |
| `r2_pullback_short_h1_confirm` | `2024` | 11 | 18.18 | 1.8386 | 0.4086 | -51.88 |
| `r2_pullback_short_h1_confirm` | `2025` | 0 | 0.00 | 0.0000 | 0.0000 | 0.00 |
| `r2_pullback_short_h1_confirm` | `2026` | 11 | 54.55 | 2.0773 | 2.4928 | 139.13 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2022` | 237 | 40.08 | 2.5766 | 1.7238 | 622.35 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2023` | 308 | 37.66 | 2.2207 | 1.3417 | 504.55 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2024` | 186 | 44.09 | 2.9547 | 2.3296 | 1979.78 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2025` | 186 | 54.30 | 1.9534 | 2.3211 | 3240.12 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2026` | 105 | 45.71 | 5.1455 | 4.3331 | 2781.65 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2022` | 140 | 46.43 | 2.7865 | 2.4149 | 806.31 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2023` | 227 | 42.29 | 2.0559 | 1.5066 | 626.57 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2024` | 181 | 45.86 | 2.7745 | 2.3498 | 2005.06 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2025` | 186 | 54.30 | 1.9534 | 2.3211 | 3240.12 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2026` | 35 | 51.43 | 10.4157 | 11.0284 | 2465.18 |

## Monthly Table

| Book | Period | Trades | WR% | W/L | PF | Net |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `r2_pullback_short_m15_confirm` | `2022-07` | 81 | 30.86 | 2.0028 | 0.8941 | -32.97 |
| `r2_pullback_short_m15_confirm` | `2022-08` | 25 | 68.00 | 2.1977 | 4.6701 | 123.61 |
| `r2_pullback_short_m15_confirm` | `2022-09` | 41 | 34.15 | 1.6443 | 0.8526 | -24.73 |
| `r2_pullback_short_m15_confirm` | `2022-10` | 33 | 36.36 | 1.9344 | 1.1054 | 10.76 |
| `r2_pullback_short_m15_confirm` | `2022-11` | 6 | 0.00 | 0.0000 | 0.0000 | -29.66 |
| `r2_pullback_short_m15_confirm` | `2023-02` | 8 | 0.00 | 0.0000 | 0.0000 | -43.64 |
| `r2_pullback_short_m15_confirm` | `2023-03` | 6 | 0.00 | 0.0000 | 0.0000 | -21.91 |
| `r2_pullback_short_m15_confirm` | `2023-06` | 48 | 27.08 | 2.4994 | 0.9283 | -13.07 |
| `r2_pullback_short_m15_confirm` | `2023-07` | 7 | 0.00 | 0.0000 | 0.0000 | -61.15 |
| `r2_pullback_short_m15_confirm` | `2023-08` | 60 | 45.00 | 2.2737 | 1.8603 | 120.43 |
| `r2_pullback_short_m15_confirm` | `2023-09` | 23 | 56.52 | 1.7341 | 2.2544 | 90.00 |
| `r2_pullback_short_m15_confirm` | `2023-10` | 29 | 13.79 | 1.6062 | 0.2570 | -84.02 |
| `r2_pullback_short_m15_confirm` | `2024-12` | 16 | 6.25 | 2.3148 | 0.1543 | -77.16 |
| `r2_pullback_short_m15_confirm` | `2026-04` | 11 | 45.45 | 3.1134 | 2.5945 | 96.58 |
| `r2_pullback_short_m15_confirm` | `2026-05` | 40 | 30.00 | 2.0049 | 0.8592 | -60.90 |
| `r2_pullback_short_m15_confirm` | `2026-06` | 30 | 63.33 | 1.8672 | 3.2251 | 419.92 |
| `r2_pullback_short_h1_confirm` | `2022-07` | 36 | 38.89 | 2.2850 | 1.4541 | 69.60 |
| `r2_pullback_short_h1_confirm` | `2022-08` | 15 | 73.33 | 2.1926 | 6.0297 | 142.49 |
| `r2_pullback_short_h1_confirm` | `2022-09` | 19 | 31.58 | 1.9636 | 0.9063 | -9.29 |
| `r2_pullback_short_h1_confirm` | `2022-10` | 18 | 38.89 | 2.3972 | 1.5255 | 35.12 |
| `r2_pullback_short_h1_confirm` | `2022-11` | 1 | 0.00 | 0.0000 | 0.0000 | -6.95 |
| `r2_pullback_short_h1_confirm` | `2023-02` | 5 | 0.00 | 0.0000 | 0.0000 | -28.83 |
| `r2_pullback_short_h1_confirm` | `2023-03` | 2 | 0.00 | 0.0000 | 0.0000 | -8.54 |
| `r2_pullback_short_h1_confirm` | `2023-06` | 30 | 40.00 | 1.5691 | 1.0461 | 6.03 |
| `r2_pullback_short_h1_confirm` | `2023-07` | 2 | 0.00 | 0.0000 | 0.0000 | -7.03 |
| `r2_pullback_short_h1_confirm` | `2023-08` | 34 | 55.88 | 1.9456 | 2.4644 | 150.10 |
| `r2_pullback_short_h1_confirm` | `2023-09` | 18 | 33.33 | 3.7997 | 1.8998 | 53.63 |
| `r2_pullback_short_h1_confirm` | `2023-10` | 9 | 0.00 | 0.0000 | 0.0000 | -56.70 |
| `r2_pullback_short_h1_confirm` | `2024-12` | 11 | 18.18 | 1.8386 | 0.4086 | -51.88 |
| `r2_pullback_short_h1_confirm` | `2026-04` | 2 | 100.00 | 0.0000 | 0.0000 | 74.02 |
| `r2_pullback_short_h1_confirm` | `2026-05` | 4 | 50.00 | 2.5452 | 2.5452 | 51.47 |
| `r2_pullback_short_h1_confirm` | `2026-06` | 5 | 40.00 | 1.8416 | 1.2278 | 13.64 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2022-07` | 81 | 30.86 | 2.0028 | 0.8941 | -32.97 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2022-08` | 25 | 68.00 | 2.1977 | 4.6701 | 123.61 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2022-09` | 41 | 34.15 | 1.6443 | 0.8526 | -24.73 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2022-10` | 33 | 36.36 | 1.9344 | 1.1054 | 10.76 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2022-11` | 10 | 20.00 | 7.1980 | 1.7995 | 52.08 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2022-12` | 47 | 53.19 | 3.2950 | 3.7444 | 493.60 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2023-01` | 38 | 44.74 | 1.9763 | 1.5998 | 225.06 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2023-02` | 16 | 6.25 | 0.8503 | 0.0567 | -116.48 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2023-03` | 13 | 0.00 | 0.0000 | 0.0000 | -61.66 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2023-04` | 12 | 41.67 | 0.8338 | 0.5956 | -38.61 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2023-05` | 6 | 33.33 | 1.2989 | 0.6495 | -14.13 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2023-06` | 48 | 27.08 | 2.4994 | 0.9283 | -13.07 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2023-07` | 12 | 0.00 | 0.0000 | 0.0000 | -95.42 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2023-08` | 60 | 45.00 | 2.2737 | 1.8603 | 120.43 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2023-09` | 23 | 56.52 | 1.7341 | 2.2544 | 90.00 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2023-10` | 33 | 12.12 | 1.4968 | 0.2065 | -111.70 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2023-11` | 29 | 68.97 | 4.4663 | 9.9250 | 403.59 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2023-12` | 18 | 77.78 | 0.6030 | 2.1106 | 116.54 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2024-02` | 5 | 0.00 | 0.0000 | 0.0000 | -18.24 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2024-03` | 27 | 100.00 | 0.0000 | 0.0000 | 1155.04 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2024-05` | 13 | 46.15 | 0.7478 | 0.6410 | -37.72 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2024-07` | 25 | 36.00 | 2.4482 | 1.3771 | 106.62 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2024-08` | 14 | 14.29 | 5.4616 | 0.9103 | -14.08 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2024-09` | 46 | 50.00 | 3.9857 | 3.9857 | 907.43 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2024-10` | 39 | 35.90 | 1.6654 | 0.9326 | -35.32 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2024-12` | 17 | 5.88 | 2.2981 | 0.1436 | -83.95 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2025-01` | 32 | 62.50 | 5.0070 | 8.3450 | 1149.56 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2025-02` | 21 | 57.14 | 2.9489 | 3.9319 | 582.12 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2025-03` | 28 | 60.71 | 1.4194 | 2.1936 | 367.36 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2025-04` | 6 | 16.67 | 2.2768 | 0.4554 | -51.24 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2025-06` | 7 | 14.29 | 0.4448 | 0.0741 | -259.16 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2025-07` | 11 | 45.45 | 1.1246 | 0.9372 | -4.73 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2025-08` | 19 | 68.42 | 2.6069 | 5.6483 | 682.32 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2025-09` | 24 | 54.17 | 2.3672 | 2.7976 | 220.17 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2025-11` | 10 | 70.00 | 1.7287 | 4.0336 | 129.90 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2025-12` | 28 | 42.86 | 1.8828 | 1.4121 | 423.82 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2026-01` | 20 | 60.00 | 17.8759 | 26.8138 | 2386.23 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2026-02` | 3 | 0.00 | 0.0000 | 0.0000 | -50.02 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2026-03` | 1 | 0.00 | 0.0000 | 0.0000 | -10.16 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2026-04` | 11 | 45.45 | 3.1134 | 2.5945 | 96.58 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2026-05` | 40 | 30.00 | 2.0049 | 0.8592 | -60.90 |
| `current_r1_plus_r2_pullback_short_m15_confirm` | `2026-06` | 30 | 63.33 | 1.8672 | 3.2251 | 419.92 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2022-07` | 36 | 38.89 | 2.2850 | 1.4541 | 69.60 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2022-08` | 15 | 73.33 | 2.1926 | 6.0297 | 142.49 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2022-09` | 19 | 31.58 | 1.9636 | 0.9063 | -9.29 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2022-10` | 18 | 38.89 | 2.3972 | 1.5255 | 35.12 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2022-11` | 5 | 40.00 | 4.1440 | 2.7627 | 74.79 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2022-12` | 47 | 53.19 | 3.2950 | 3.7444 | 493.60 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2023-01` | 38 | 44.74 | 1.9763 | 1.5998 | 225.06 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2023-02` | 13 | 7.69 | 0.7730 | 0.0644 | -101.67 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2023-03` | 9 | 0.00 | 0.0000 | 0.0000 | -48.29 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2023-04` | 12 | 41.67 | 0.8338 | 0.5956 | -38.61 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2023-05` | 6 | 33.33 | 1.2989 | 0.6495 | -14.13 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2023-06` | 30 | 40.00 | 1.5691 | 1.0461 | 6.03 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2023-07` | 7 | 0.00 | 0.0000 | 0.0000 | -41.30 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2023-08` | 34 | 55.88 | 1.9456 | 2.4644 | 150.10 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2023-09` | 18 | 33.33 | 3.7997 | 1.8998 | 53.63 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2023-10` | 13 | 0.00 | 0.0000 | 0.0000 | -84.38 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2023-11` | 29 | 68.97 | 4.4663 | 9.9250 | 403.59 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2023-12` | 18 | 77.78 | 0.6030 | 2.1106 | 116.54 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2024-02` | 5 | 0.00 | 0.0000 | 0.0000 | -18.24 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2024-03` | 27 | 100.00 | 0.0000 | 0.0000 | 1155.04 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2024-05` | 13 | 46.15 | 0.7478 | 0.6410 | -37.72 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2024-07` | 25 | 36.00 | 2.4482 | 1.3771 | 106.62 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2024-08` | 14 | 14.29 | 5.4616 | 0.9103 | -14.08 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2024-09` | 46 | 50.00 | 3.9857 | 3.9857 | 907.43 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2024-10` | 39 | 35.90 | 1.6654 | 0.9326 | -35.32 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2024-12` | 12 | 16.67 | 1.8961 | 0.3792 | -58.67 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2025-01` | 32 | 62.50 | 5.0070 | 8.3450 | 1149.56 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2025-02` | 21 | 57.14 | 2.9489 | 3.9319 | 582.12 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2025-03` | 28 | 60.71 | 1.4194 | 2.1936 | 367.36 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2025-04` | 6 | 16.67 | 2.2768 | 0.4554 | -51.24 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2025-06` | 7 | 14.29 | 0.4448 | 0.0741 | -259.16 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2025-07` | 11 | 45.45 | 1.1246 | 0.9372 | -4.73 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2025-08` | 19 | 68.42 | 2.6069 | 5.6483 | 682.32 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2025-09` | 24 | 54.17 | 2.3672 | 2.7976 | 220.17 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2025-11` | 10 | 70.00 | 1.7287 | 4.0336 | 129.90 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2025-12` | 28 | 42.86 | 1.8828 | 1.4121 | 423.82 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2026-01` | 20 | 60.00 | 17.8759 | 26.8138 | 2386.23 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2026-02` | 3 | 0.00 | 0.0000 | 0.0000 | -50.02 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2026-03` | 1 | 0.00 | 0.0000 | 0.0000 | -10.16 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2026-04` | 2 | 100.00 | 0.0000 | 0.0000 | 74.02 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2026-05` | 4 | 50.00 | 2.5452 | 2.5452 | 51.47 |
| `current_r1_plus_r2_pullback_short_h1_confirm` | `2026-06` | 5 | 40.00 | 1.8416 | 1.2278 | 13.64 |

## Failed Checks

- `r2_pullback_short_m15_confirm`: wr_ge_45_watchlist, wr_ge_50_true_pass, pf_ge_1p25, stress_pf_ge_1p15, top10_removed_net_gt_0, top3_days_removed_net_gt_0, best_month_share_lte_35pct, y2023_2024_nonnegative_if_exposed
- `r2_pullback_short_h1_confirm`: wr_ge_45_watchlist, wr_ge_50_true_pass, best_month_share_lte_35pct
- `current_r1_plus_r2_pullback_short_m15_confirm`: wr_ge_49
- `current_r1_plus_r2_pullback_short_h1_confirm`: wr_ge_49

## Stop Path Checks

- `r2_pullback_short_m15_confirm`: wr_lt_40, top10_removed_net_lte_0, top3_days_removed_net_lte_0
- `r2_pullback_short_h1_confirm`: wr_lt_40

## Static Validation

- `variant_count_eq_2`: True
- `all_strict_r2_router`: True
- `all_short_only`: True
- `all_signal_21`: True
- `all_rr_2`: True
- `no_session_filter`: True
- `no_hour_day_filters`: True
- `no_breakeven_partial_trailing`: True

## Interpretation

At least one strict R2 variant was positive, but no variant cleared the full standalone-plus-combined gate set. Keep as research-only shadow evidence.

## Artifacts

- report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_PULLBACK_REJECTION_SHORT_V1_EXACT_20260708.md`
- report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_PULLBACK_REJECTION_SHORT_V1_EXACT_20260708.json`
- standalone_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_PULLBACK_REJECTION_SHORT_V1_EXACT_20260708_STANDALONE.csv`
- combined_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_PULLBACK_REJECTION_SHORT_V1_EXACT_20260708_COMBINED.csv`
- mt5_components_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_PULLBACK_REJECTION_SHORT_V1_EXACT_20260708_MT5_COMPONENTS.md`
- mt5_components_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_PULLBACK_REJECTION_SHORT_V1_EXACT_20260708_MT5_COMPONENTS.json`
- r2_pullback_short_m15_confirm_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_PULLBACK_REJECTION_SHORT_V1_EXACT_20260708_r2_pullback_short_m15_confirm_NORMALIZED_TRADES.csv`
- r2_pullback_short_h1_confirm_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_PULLBACK_REJECTION_SHORT_V1_EXACT_20260708_r2_pullback_short_h1_confirm_NORMALIZED_TRADES.csv`
- current_r1_plus_r2_pullback_short_m15_confirm_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_PULLBACK_REJECTION_SHORT_V1_EXACT_20260708_current_r1_plus_r2_pullback_short_m15_confirm_KEPT.csv`
- current_r1_plus_r2_pullback_short_m15_confirm_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_PULLBACK_REJECTION_SHORT_V1_EXACT_20260708_current_r1_plus_r2_pullback_short_m15_confirm_DROPPED.csv`
- current_r1_plus_r2_pullback_short_h1_confirm_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_PULLBACK_REJECTION_SHORT_V1_EXACT_20260708_current_r1_plus_r2_pullback_short_h1_confirm_KEPT.csv`
- current_r1_plus_r2_pullback_short_h1_confirm_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_PULLBACK_REJECTION_SHORT_V1_EXACT_20260708_current_r1_plus_r2_pullback_short_h1_confirm_DROPPED.csv`
