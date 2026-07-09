# A1 XAU R2 Continuation Short V2 Repair Exact-MT5

Generated UTC: `2026-07-08T22:03:47Z`
Status: `R2_CONTINUATION_SHORT_V2_REPAIR_SHADOW_ONLY`

Scope: exact-MT5 research-only repair of the strict-R2 continuation short specialist. No demo/live runtime, chart, preset, order, position, account, or broker state was changed.

Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_R2_CONTINUATION_SHORT_V2_REPAIR_PREREG_2026_07_09.md`
Preregistration SHA256: `0cf013f77a5295c08d543c5576af81cc3e13d4cbc917f59b2e75fc0d9287d9f9`
Best repaired R2 pullback book: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_PULLBACK_REJECTION_SHORT_V2_REPAIR_EXACT_20260709_r2_h1_m5_body58_hours05_18_NORMALIZED_TRADES.csv`
MT5 component evidence: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V2_REPAIR_EXACT_20260709_MT5_COMPONENTS.md`

## Baseline Book

| Book | Trades | WR% | W/L | PF | Net | Recent3 trades | Recent3 WR% | Recent3 PF | Recent3 net | Max DD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `current_r1_plus_best_r2_pullback` | 621 | 50.40 | 2.6639 | 2.7072 | 9050.59 | 4 | 100.00 | 0.0000 | 148.48 | 889.69 |

## Standalone Full Window

| Variant | Trades | Wins | Losses | WR% | W/L | PF | Net | Stress PF | Stress net | Max DD | Top10 rem | Top3 days rem | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `r2_impulse_break20_cap25` | 88 | 32 | 56 | 36.36 | 2.6779 | 1.5302 | 175.74 | 1.4288 | 149.34 | 83.92 | -123.12 | -50.81 | False |
| `r2_impulse_break15_30_cap20` | 150 | 55 | 95 | 36.67 | 2.4707 | 1.4304 | 229.52 | 1.3285 | 184.52 | 100.61 | -80.40 | -37.48 | False |
| `r2_impulse_q55_break20_cap25` | 48 | 19 | 29 | 39.58 | 2.4382 | 1.5974 | 109.66 | 1.4955 | 95.26 | 45.87 | -120.49 | -20.40 | False |

## Standalone Last Three Months

| Variant | Recent3 trades | Recent3 WR% | Recent3 W/L | Recent3 PF | Recent3 net | June trades | June WR% | June PF | June net |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `r2_impulse_break20_cap25` | 18 | 61.11 | 1.6659 | 2.6178 | 195.77 | 13 | 69.23 | 3.5781 | 182.22 |
| `r2_impulse_break15_30_cap20` | 33 | 54.55 | 1.9759 | 2.3711 | 278.75 | 25 | 60.00 | 2.7769 | 256.99 |
| `r2_impulse_q55_break20_cap25` | 10 | 60.00 | 1.8780 | 2.8170 | 121.10 | 7 | 71.43 | 4.2923 | 119.97 |

## Combined With Current R1 Plus Best R2 Pullback

| Book | Trades | WR% | W/L | PF | Net | Recent3 trades | Recent3 WR% | Recent3 PF | Recent3 net | Max DD | Dropped | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `current_r1_best_r2_pullback_plus_r2_impulse_break20_cap25` | 705 | 48.79 | 2.7754 | 2.6447 | 9234.54 | 22 | 68.18 | 3.8448 | 344.25 | 889.69 | 4 | False |
| `current_r1_best_r2_pullback_plus_r2_impulse_break15_30_cap20` | 762 | 47.90 | 2.8276 | 2.5997 | 9282.14 | 37 | 59.46 | 3.1014 | 427.23 | 889.69 | 9 | False |
| `current_r1_best_r2_pullback_plus_r2_impulse_q55_break20_cap25` | 666 | 49.70 | 2.7069 | 2.6746 | 9163.39 | 14 | 71.43 | 5.0447 | 269.58 | 889.69 | 3 | False |

## Failed Checks

- `r2_impulse_break20_cap25` standalone: wr_ge_50, top10_removed_net_gt_0, top3_days_removed_net_gt_0
- `r2_impulse_break15_30_cap20` standalone: wr_ge_50, pf_ge_1p50, top10_removed_net_gt_0, top3_days_removed_net_gt_0
- `r2_impulse_q55_break20_cap25` standalone: wr_ge_50, top10_removed_net_gt_0, top3_days_removed_net_gt_0
- `current_r1_best_r2_pullback_plus_r2_impulse_break20_cap25` combined: wr_ge_50
- `current_r1_best_r2_pullback_plus_r2_impulse_break15_30_cap20` combined: wr_ge_50
- `current_r1_best_r2_pullback_plus_r2_impulse_q55_break20_cap25` combined: wr_ge_50

## Yearly Table

| Book | Period | Trades | WR% | W/L | PF | Net |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `r2_impulse_break20_cap25` | `2022` | 41 | 24.39 | 2.0136 | 0.6495 | -47.96 |
| `r2_impulse_break20_cap25` | `2023` | 28 | 39.29 | 2.3522 | 1.5220 | 34.82 |
| `r2_impulse_break20_cap25` | `2024` | 1 | 0.00 | 0.0000 | 0.0000 | -6.89 |
| `r2_impulse_break20_cap25` | `2025` | 0 | 0.00 | 0.0000 | 0.0000 | 0.00 |
| `r2_impulse_break20_cap25` | `2026` | 18 | 61.11 | 1.6659 | 2.6178 | 195.77 |
| `r2_impulse_break15_30_cap20` | `2022` | 60 | 28.33 | 1.9007 | 0.7514 | -42.25 |
| `r2_impulse_break15_30_cap20` | `2023` | 51 | 35.29 | 1.9869 | 1.0838 | 10.74 |
| `r2_impulse_break15_30_cap20` | `2024` | 5 | 40.00 | 1.4790 | 0.9860 | -0.20 |
| `r2_impulse_break15_30_cap20` | `2025` | 0 | 0.00 | 0.0000 | 0.0000 | 0.00 |
| `r2_impulse_break15_30_cap20` | `2026` | 34 | 52.94 | 1.9404 | 2.1829 | 261.23 |
| `r2_impulse_q55_break20_cap25` | `2022` | 19 | 36.84 | 1.6572 | 0.9667 | -1.75 |
| `r2_impulse_q55_break20_cap25` | `2023` | 17 | 35.29 | 2.0858 | 1.1377 | 6.62 |
| `r2_impulse_q55_break20_cap25` | `2024` | 2 | 0.00 | 0.0000 | 0.0000 | -16.31 |
| `r2_impulse_q55_break20_cap25` | `2025` | 0 | 0.00 | 0.0000 | 0.0000 | 0.00 |
| `r2_impulse_q55_break20_cap25` | `2026` | 10 | 60.00 | 1.8780 | 2.8170 | 121.10 |
| `current_r1_best_r2_pullback_plus_r2_impulse_break20_cap25` | `2022` | 118 | 40.68 | 3.2674 | 2.2405 | 583.06 |
| `current_r1_best_r2_pullback_plus_r2_impulse_break20_cap25` | `2023` | 183 | 46.99 | 1.8959 | 1.6809 | 683.19 |
| `current_r1_best_r2_pullback_plus_r2_impulse_break20_cap25` | `2024` | 172 | 47.67 | 2.6936 | 2.4542 | 2057.87 |
| `current_r1_best_r2_pullback_plus_r2_impulse_break20_cap25` | `2025` | 186 | 54.30 | 1.9534 | 2.3211 | 3240.12 |
| `current_r1_best_r2_pullback_plus_r2_impulse_break20_cap25` | `2026` | 46 | 58.70 | 7.5710 | 10.7588 | 2670.30 |
| `current_r1_best_r2_pullback_plus_r2_impulse_break15_30_cap20` | `2022` | 135 | 40.74 | 3.2465 | 2.2319 | 602.69 |
| `current_r1_best_r2_pullback_plus_r2_impulse_break15_30_cap20` | `2023` | 202 | 45.05 | 1.9646 | 1.6106 | 645.90 |
| `current_r1_best_r2_pullback_plus_r2_impulse_break15_30_cap20` | `2024` | 177 | 47.46 | 2.7008 | 2.4395 | 2057.67 |
| `current_r1_best_r2_pullback_plus_r2_impulse_break15_30_cap20` | `2025` | 186 | 54.30 | 1.9534 | 2.3211 | 3240.12 |
| `current_r1_best_r2_pullback_plus_r2_impulse_break15_30_cap20` | `2026` | 62 | 54.84 | 6.8564 | 8.3256 | 2735.76 |
| `current_r1_best_r2_pullback_plus_r2_impulse_q55_break20_cap25` | `2022` | 96 | 46.88 | 2.9785 | 2.6281 | 628.76 |
| `current_r1_best_r2_pullback_plus_r2_impulse_q55_break20_cap25` | `2023` | 173 | 46.82 | 1.8797 | 1.6549 | 648.91 |
| `current_r1_best_r2_pullback_plus_r2_impulse_q55_break20_cap25` | `2024` | 173 | 47.40 | 2.7084 | 2.4405 | 2049.97 |
| `current_r1_best_r2_pullback_plus_r2_impulse_q55_break20_cap25` | `2025` | 186 | 54.30 | 1.9534 | 2.3211 | 3240.12 |
| `current_r1_best_r2_pullback_plus_r2_impulse_q55_break20_cap25` | `2026` | 38 | 57.89 | 9.3364 | 12.8376 | 2595.63 |

## Guard Summary

### `r2_impulse_break20_cap25`
- `break_distance_atr_below_floor`: 2764
- `break_distance_atr_exceeds_cap`: 24
- `regime_router_block_short_r2_downtrend_only_state_chop`: 288
- `regime_router_block_short_r2_downtrend_only_state_compression`: 66
- `regime_router_block_short_r2_downtrend_only_state_shock`: 126
- `regime_router_block_short_r2_downtrend_only_state_uptrend`: 173
- `stop_ceiling_exceeded`: 6
- `three_bar_move_atr_exceeds_cap`: 346

### `r2_impulse_break15_30_cap20`
- `break_distance_atr_below_floor`: 1967
- `break_distance_atr_exceeds_cap`: 99
- `regime_router_block_short_r2_downtrend_only_state_chop`: 423
- `regime_router_block_short_r2_downtrend_only_state_compression`: 117
- `regime_router_block_short_r2_downtrend_only_state_shock`: 161
- `regime_router_block_short_r2_downtrend_only_state_uptrend`: 245
- `stop_ceiling_exceeded`: 5
- `three_bar_move_atr_exceeds_cap`: 714

### `r2_impulse_q55_break20_cap25`
- `break_distance_atr_below_floor`: 1341
- `break_distance_atr_exceeds_cap`: 16
- `regime_router_block_short_r2_downtrend_only_state_chop`: 166
- `regime_router_block_short_r2_downtrend_only_state_compression`: 38
- `regime_router_block_short_r2_downtrend_only_state_shock`: 74
- `regime_router_block_short_r2_downtrend_only_state_uptrend`: 110
- `stop_ceiling_exceeded`: 6
- `three_bar_move_atr_exceeds_cap`: 174

## Interpretation

At least one V2 repair variant was profitable and recent-period safe, but no variant cleared standalone and combined gates.

## Artifacts

- report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V2_REPAIR_EXACT_20260709.md`
- report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V2_REPAIR_EXACT_20260709.json`
- standalone_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V2_REPAIR_EXACT_20260709_STANDALONE.csv`
- combined_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V2_REPAIR_EXACT_20260709_COMBINED.csv`
- mt5_components_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V2_REPAIR_EXACT_20260709_MT5_COMPONENTS.md`
- mt5_components_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V2_REPAIR_EXACT_20260709_MT5_COMPONENTS.json`
- r2_impulse_break20_cap25_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V2_REPAIR_EXACT_20260709_r2_impulse_break20_cap25_NORMALIZED_TRADES.csv`
- r2_impulse_break15_30_cap20_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V2_REPAIR_EXACT_20260709_r2_impulse_break15_30_cap20_NORMALIZED_TRADES.csv`
- r2_impulse_q55_break20_cap25_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V2_REPAIR_EXACT_20260709_r2_impulse_q55_break20_cap25_NORMALIZED_TRADES.csv`
- current_r1_best_r2_pullback_plus_r2_impulse_break20_cap25_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V2_REPAIR_EXACT_20260709_current_r1_best_r2_pullback_plus_r2_impulse_break20_cap25_KEPT.csv`
- current_r1_best_r2_pullback_plus_r2_impulse_break20_cap25_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V2_REPAIR_EXACT_20260709_current_r1_best_r2_pullback_plus_r2_impulse_break20_cap25_DROPPED.csv`
- current_r1_best_r2_pullback_plus_r2_impulse_break15_30_cap20_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V2_REPAIR_EXACT_20260709_current_r1_best_r2_pullback_plus_r2_impulse_break15_30_cap20_KEPT.csv`
- current_r1_best_r2_pullback_plus_r2_impulse_break15_30_cap20_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V2_REPAIR_EXACT_20260709_current_r1_best_r2_pullback_plus_r2_impulse_break15_30_cap20_DROPPED.csv`
- current_r1_best_r2_pullback_plus_r2_impulse_q55_break20_cap25_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V2_REPAIR_EXACT_20260709_current_r1_best_r2_pullback_plus_r2_impulse_q55_break20_cap25_KEPT.csv`
- current_r1_best_r2_pullback_plus_r2_impulse_q55_break20_cap25_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V2_REPAIR_EXACT_20260709_current_r1_best_r2_pullback_plus_r2_impulse_q55_break20_cap25_DROPPED.csv`
