# A1 XAU Short V2 Robustness Exact MT5 Pass

Generated UTC: `2026-07-07T22:10:38Z`
Status: `NO_DURABLE_STANDALONE_SHORT_EDGE`

Scope: exact-MT5 robustness pass for `short_hedge_v2_breakdown_retest`. The pass changes only the preregistered D1 regime definition across R1/R2/R3; no session/hour/day/month filters or post-result quality filters were added.

Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_SHORT_V2_ROBUSTNESS_PREREG_2026_07_08.md`
Preregistration SHA256: `58d839356a8d43a159628e77a96424df6e3bf31f87134fc6c70adf6bedc8b502`

## T1 Regime Results

| Variant | Trades | WR% | W/L | PF | Net | Stress PF | Stress net | Pos year buckets | 2023+2024 net | Top10-removed net | Top3-days-removed net | T1 | Conc. |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `short_v2_r1_d1_ema20_bearish` | 329 | 32.83 | 2.8332 | 1.3846 | 441.42 | 1.2823 | 342.72 | 3 | -192.69 | 103.72 | 176.76 | FAIL | PASS |
| `short_v2_r2_d1_ema20_nonup` | 393 | 33.84 | 2.6537 | 1.3574 | 507.56 | 1.2601 | 389.66 | 3 | -166.41 | 162.93 | 242.90 | FAIL | PASS |
| `short_v2_r3_d1_ema50_structural_down` | 242 | 36.36 | 2.4720 | 1.4126 | 345.72 | 1.3089 | 273.12 | 2 | -77.52 | 34.48 | 148.46 | FAIL | PASS |

## By Year

### `short_v2_r1_d1_ema20_bearish`

| Year | Trades | WR% | W/L | PF | Net |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2022 | 79 | 36.71 | 2.0712 | 1.2013 | 41.34 |
| 2023 | 117 | 26.50 | 1.9750 | 0.7119 | -92.66 |
| 2024 | 58 | 17.24 | 2.7026 | 0.5630 | -100.03 |
| 2025 | 21 | 38.10 | 3.7600 | 2.3138 | 104.87 |
| 2026 | 54 | 55.56 | 2.0505 | 2.5631 | 487.90 |

### `short_v2_r2_d1_ema20_nonup`

| Year | Trades | WR% | W/L | PF | Net |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2022 | 85 | 36.47 | 2.0700 | 1.1884 | 41.32 |
| 2023 | 128 | 30.47 | 1.9994 | 0.8761 | -41.21 |
| 2024 | 67 | 16.42 | 2.6512 | 0.5208 | -125.20 |
| 2025 | 53 | 35.85 | 2.6121 | 1.4597 | 113.59 |
| 2026 | 60 | 55.00 | 1.9993 | 2.4436 | 519.06 |

### `short_v2_r3_d1_ema50_structural_down`

| Year | Trades | WR% | W/L | PF | Net |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2022 | 83 | 36.14 | 2.0764 | 1.1753 | 37.84 |
| 2023 | 90 | 31.11 | 2.0097 | 0.9076 | -21.65 |
| 2024 | 18 | 16.67 | 1.4455 | 0.2891 | -55.87 |
| 2025 | 1 | 0.00 | 0.0000 | 0.0000 | -3.52 |
| 2026 | 50 | 54.00 | 1.9356 | 2.2722 | 388.92 |

## Walk-Forward Blocks

### `short_v2_r1_d1_ema20_bearish`

T2 preview: `4/8` nonnegative blocks, max block share `110.53`, early positive block `True`.

| Block | Start | End | Trades | WR% | W/L | PF | Net |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| B1 | 2022-07-01 | 2022-12-31 | 79 | 36.71 | 2.0712 | 1.2013 | 41.34 |
| B2 | 2023-01-01 | 2023-06-30 | 68 | 23.53 | 2.0933 | 0.6441 | -67.09 |
| B3 | 2023-07-01 | 2023-12-31 | 49 | 30.61 | 1.8313 | 0.8079 | -25.57 |
| B4 | 2024-01-01 | 2024-06-30 | 31 | 9.68 | 2.2753 | 0.2438 | -96.41 |
| B5 | 2024-07-01 | 2024-12-31 | 27 | 25.93 | 2.7552 | 0.9643 | -3.62 |
| B6 | 2025-01-01 | 2025-06-30 | 12 | 33.33 | 4.2211 | 2.1106 | 45.60 |
| B7 | 2025-07-01 | 2025-12-31 | 9 | 44.44 | 3.1614 | 2.5292 | 59.27 |
| B8 | 2026-01-01 | 2026-06-30 | 54 | 55.56 | 2.0505 | 2.5631 | 487.90 |

### `short_v2_r2_d1_ema20_nonup`

T2 preview: `5/8` nonnegative blocks, max block share `102.27`, early positive block `True`.

| Block | Start | End | Trades | WR% | W/L | PF | Net |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| B1 | 2022-07-01 | 2022-12-31 | 85 | 36.47 | 2.0700 | 1.1884 | 41.32 |
| B2 | 2023-01-01 | 2023-06-30 | 71 | 23.94 | 2.0866 | 0.6569 | -67.08 |
| B3 | 2023-07-01 | 2023-12-31 | 57 | 38.60 | 1.8910 | 1.1886 | 25.87 |
| B4 | 2024-01-01 | 2024-06-30 | 35 | 8.57 | 2.3302 | 0.2185 | -111.19 |
| B5 | 2024-07-01 | 2024-12-31 | 32 | 25.00 | 2.6467 | 0.8822 | -14.01 |
| B6 | 2025-01-01 | 2025-06-30 | 31 | 35.48 | 2.4359 | 1.3397 | 42.44 |
| B7 | 2025-07-01 | 2025-12-31 | 22 | 36.36 | 2.7691 | 1.5823 | 71.15 |
| B8 | 2026-01-01 | 2026-06-30 | 60 | 55.00 | 1.9993 | 2.4436 | 519.06 |

### `short_v2_r3_d1_ema50_structural_down`

T2 preview: `4/8` nonnegative blocks, max block share `112.5`, early positive block `True`.

| Block | Start | End | Trades | WR% | W/L | PF | Net |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| B1 | 2022-07-01 | 2022-12-31 | 83 | 36.14 | 2.0764 | 1.1753 | 37.84 |
| B2 | 2023-01-01 | 2023-06-30 | 50 | 24.00 | 2.1679 | 0.6846 | -43.00 |
| B3 | 2023-07-01 | 2023-12-31 | 40 | 40.00 | 1.8270 | 1.2180 | 21.35 |
| B4 | 2024-01-01 | 2024-06-30 | 2 | 0.00 | 0.0000 | 0.0000 | -7.03 |
| B5 | 2024-07-01 | 2024-12-31 | 16 | 18.75 | 1.3758 | 0.3175 | -48.84 |
| B6 | 2025-01-01 | 2025-06-30 | 1 | 0.00 | 0.0000 | 0.0000 | -3.52 |
| B7 | 2025-07-01 | 2025-12-31 | 0 | 0.00 | 0.0000 | 0.0000 | 0.00 |
| B8 | 2026-01-01 | 2026-06-30 | 50 | 54.00 | 1.9356 | 2.2722 | 388.92 |

## Decision

No preregistered D1 regime definition passed T1. The standalone breakdown-retest short did not close the 2023-2024 stability hole while preserving positive full-window/stress/frequency gates. Per the work order, downgrade it to combined-portfolio hedge-only and stop standalone short iteration.

## R1 Parity

- `signals_match`: `PASS`
- `wr_match`: `PASS`
- `wl_match`: `PASS`
- `pf_match`: `PASS`
- `net_match`: `PASS`

## Artifacts

- md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_V2_ROBUSTNESS_20260708.md`
- json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_V2_ROBUSTNESS_20260708.json`
- summary_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_V2_ROBUSTNESS_20260708_SUMMARY.csv`
- year_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_V2_ROBUSTNESS_20260708_YEAR.csv`
- block_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_V2_ROBUSTNESS_20260708_BLOCK.csv`
- mt5_components_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_V2_ROBUSTNESS_20260708_MT5_COMPONENTS.md`
- mt5_components_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_V2_ROBUSTNESS_20260708_MT5_COMPONENTS.json`
- short_v2_r1_d1_ema20_bearish_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_V2_ROBUSTNESS_20260708_short_v2_r1_d1_ema20_bearish_NORMALIZED_TRADES.csv`
- short_v2_r2_d1_ema20_nonup_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_V2_ROBUSTNESS_20260708_short_v2_r2_d1_ema20_nonup_NORMALIZED_TRADES.csv`
- short_v2_r3_d1_ema50_structural_down_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_V2_ROBUSTNESS_20260708_short_v2_r3_d1_ema50_structural_down_NORMALIZED_TRADES.csv`
