# A1 XAU Short WR50 RR2 Exact MT5 Probe

Generated UTC: `2026-07-07T22:25:19Z`
Status: `NO_SHORT_WR50_RR2_SURVIVOR`

Scope: fixed-RR2 short expert probe for 50% win rate. All variants were preregistered and run in exact MT5; no hour/session/day/month masks were used.

Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_SHORT_WR50_RR2_PREREG_2026_07_08.md`
Preregistration SHA256: `696dc210f84944d2b5085331542df1d61576040f9628c9be4a58cd02120a36b6`
Depends on V2 robustness prereg: `xau-usd/xauusd-phase1/docs/A1_XAU_SHORT_V2_ROBUSTNESS_PREREG_2026_07_08.md`

## Results

| Variant | Trades | WR% | W/L | PF | Net | Stress PF | Stress net | 2023+2024 | Top10-removed | Top3-days-removed | Pos weeks% | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `wr50_s1_m5_sweep_structural` | 84 | 34.52 | 1.9865 | 1.0474 | 14.03 | 0.9642 | -11.17 | -15.76 | -162.53 | -73.30 | 45.45 | FAIL |
| `wr50_s2_prior_day_sweep_structural` | 30 | 33.33 | 1.7615 | 0.8807 | -17.08 | 0.8252 | -26.08 | -5.73 | -143.22 | -69.66 | 42.86 | FAIL |
| `wr50_s3_ema_pullback_structural` | 377 | 31.83 | 2.0412 | 0.9531 | -80.06 | 0.8918 | -193.16 | -86.89 | -463.52 | -247.72 | 44.07 | FAIL |
| `wr50_s4_m5_ema_trend_structural` | 253 | 33.99 | 1.9600 | 1.0093 | 9.46 | 0.9376 | -66.44 | -36.98 | -325.85 | -186.69 | 38.89 | FAIL |
| `wr50_s5_v2_strict_retest_structural` | 209 | 34.45 | 2.4847 | 1.3058 | 235.05 | 1.2129 | 172.35 | -64.17 | -79.17 | 71.70 | 41.67 | FAIL |

## Gate Failures

- `wr50_s1_m5_sweep_structural`: wr_ge_50, trades_ge_100, stress_net_gt_0, stress_pf_ge_1p15, y2023_2024_net_ge_0, top10_removed_net_gt_0, top3_days_removed_net_gt_0
- `wr50_s2_prior_day_sweep_structural`: wr_ge_50, wl_ge_1p90, trades_ge_100, net_gt_0, stress_net_gt_0, stress_pf_ge_1p15, y2023_2024_net_ge_0, top10_removed_net_gt_0, top3_days_removed_net_gt_0
- `wr50_s3_ema_pullback_structural`: wr_ge_50, net_gt_0, stress_net_gt_0, stress_pf_ge_1p15, y2023_2024_net_ge_0, top10_removed_net_gt_0, top3_days_removed_net_gt_0
- `wr50_s4_m5_ema_trend_structural`: wr_ge_50, stress_net_gt_0, stress_pf_ge_1p15, y2023_2024_net_ge_0, top10_removed_net_gt_0, top3_days_removed_net_gt_0
- `wr50_s5_v2_strict_retest_structural`: wr_ge_50, y2023_2024_net_ge_0, top10_removed_net_gt_0

## By Year

### `wr50_s1_m5_sweep_structural`

| Year | Trades | WR% | W/L | PF | Net |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2022 | 24 | 41.67 | 1.9252 | 1.3751 | 19.83 |
| 2023 | 37 | 35.14 | 1.9471 | 1.0547 | 4.93 |
| 2024 | 9 | 11.11 | 2.8452 | 0.3557 | -20.69 |
| 2025 | 0 | 0.00 | 0.0000 | 0.0000 | 0.00 |
| 2026 | 14 | 35.71 | 1.9487 | 1.0826 | 9.96 |

### `wr50_s2_prior_day_sweep_structural`

| Year | Trades | WR% | W/L | PF | Net |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2022 | 7 | 57.14 | 1.4978 | 1.9971 | 20.31 |
| 2023 | 11 | 18.18 | 1.7727 | 0.3939 | -21.54 |
| 2024 | 3 | 66.67 | 2.0320 | 4.0640 | 15.81 |
| 2025 | 2 | 0.00 | 0.0000 | 0.0000 | -13.31 |
| 2026 | 7 | 28.57 | 1.8336 | 0.7334 | -18.35 |

### `wr50_s3_ema_pullback_structural`

| Year | Trades | WR% | W/L | PF | Net |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2022 | 127 | 32.28 | 1.9573 | 0.9331 | -22.78 |
| 2023 | 116 | 32.76 | 1.8942 | 0.9228 | -23.76 |
| 2024 | 34 | 20.59 | 1.9616 | 0.5086 | -63.13 |
| 2025 | 7 | 14.29 | 2.2723 | 0.3787 | -21.90 |
| 2026 | 93 | 35.48 | 1.9228 | 1.0575 | 51.51 |

### `wr50_s4_m5_ema_trend_structural`

| Year | Trades | WR% | W/L | PF | Net |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2022 | 91 | 34.07 | 1.8970 | 0.9801 | -4.58 |
| 2023 | 92 | 33.70 | 1.8278 | 0.9289 | -17.47 |
| 2024 | 17 | 23.53 | 2.1895 | 0.6737 | -19.51 |
| 2025 | 3 | 33.33 | 2.4105 | 1.2053 | 2.26 |
| 2026 | 50 | 38.00 | 1.8018 | 1.1043 | 48.76 |

### `wr50_s5_v2_strict_retest_structural`

| Year | Trades | WR% | W/L | PF | Net |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2022 | 78 | 33.33 | 2.1595 | 1.0797 | 16.81 |
| 2023 | 72 | 30.56 | 2.2127 | 0.9736 | -4.89 |
| 2024 | 16 | 12.50 | 1.3451 | 0.1922 | -59.28 |
| 2025 | 1 | 0.00 | 0.0000 | 0.0000 | -3.52 |
| 2026 | 42 | 52.38 | 1.7879 | 1.9667 | 285.93 |

## Decision

No preregistered existing-signal proxy reached 50% WR with fixed RR2 and the durability/frequency gates. Best WR was `wr50_s1_m5_sweep_structural` at 34.52% with 84 trades. Best net was `wr50_s5_v2_strict_retest_structural` at 235.05 USD. Next step, if we keep this target, is a new purpose-built lower-high/failed-rally signal implementation rather than more filtering.

## Artifacts

- md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_WR50_RR2_20260708.md`
- json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_WR50_RR2_20260708.json`
- summary_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_WR50_RR2_20260708_SUMMARY.csv`
- year_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_WR50_RR2_20260708_YEAR.csv`
- block_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_WR50_RR2_20260708_BLOCK.csv`
- mt5_components_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_WR50_RR2_20260708_MT5_COMPONENTS.md`
- mt5_components_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_WR50_RR2_20260708_MT5_COMPONENTS.json`
- wr50_s1_m5_sweep_structural_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_WR50_RR2_20260708_wr50_s1_m5_sweep_structural_NORMALIZED_TRADES.csv`
- wr50_s2_prior_day_sweep_structural_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_WR50_RR2_20260708_wr50_s2_prior_day_sweep_structural_NORMALIZED_TRADES.csv`
- wr50_s3_ema_pullback_structural_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_WR50_RR2_20260708_wr50_s3_ema_pullback_structural_NORMALIZED_TRADES.csv`
- wr50_s4_m5_ema_trend_structural_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_WR50_RR2_20260708_wr50_s4_m5_ema_trend_structural_NORMALIZED_TRADES.csv`
- wr50_s5_v2_strict_retest_structural_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_WR50_RR2_20260708_wr50_s5_v2_strict_retest_structural_NORMALIZED_TRADES.csv`
