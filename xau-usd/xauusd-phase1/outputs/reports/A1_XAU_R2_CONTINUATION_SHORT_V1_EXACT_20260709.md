# A1 XAU R2 Continuation Short V1 Exact-MT5

Generated UTC: `2026-07-08T21:47:12Z`
Status: `R2_CONTINUATION_SHORT_V1_SHADOW_ONLY`

Scope: exact-MT5 research-only test for a second strict-R2 short specialist. No demo/live runtime, chart, preset, order, position, account, or broker state was changed.

Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_R2_CONTINUATION_SHORT_V1_PREREG_2026_07_09.md`
Preregistration SHA256: `b908a15f3fd91f35247305c81f61abdf14624190ca580fb6b01d8025ad5d99a3`
Current R1 book: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_PULLBACK_LONG_V2_SESSION_EXACT_20260708_box_plus_r1_pullback_long_v2_m15_session_09_15_KEPT.csv`
Best repaired R2 pullback book: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_PULLBACK_REJECTION_SHORT_V2_REPAIR_EXACT_20260709_r2_h1_m5_body58_hours05_18_NORMALIZED_TRADES.csv`
MT5 component evidence: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V1_EXACT_20260709_MT5_COMPONENTS.md`

## Baseline Book

| Book | Trades | WR% | W/L | PF | Net | Recent3 trades | Recent3 WR% | Recent3 PF | Recent3 net | Max DD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `current_r1_plus_best_r2_pullback` | 621 | 50.40 | 2.6639 | 2.7072 | 9050.59 | 4 | 100.00 | 0.0000 | 148.48 | 889.69 |

## Standalone Continuation Full Window

| Variant | Trades | Wins | Losses | WR% | W/L | PF | Net | Stress W/L | Stress PF | Stress net | Max DD | Top10 rem | Top3 days rem | Best month% | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `r2_break_retest_body45` | 676 | 239 | 437 | 35.36 | 2.3571 | 1.2891 | 629.26 | 2.1664 | 1.1848 | 426.46 | 230.79 | 252.10 | -123.48 | 104.26 | False |
| `r2_impulse_retest_body45` | 454 | 165 | 289 | 36.34 | 2.5665 | 1.4653 | 666.43 | 2.3629 | 1.3491 | 530.23 | 233.25 | 298.02 | 54.57 | 94.35 | False |
| `r2_impulse_retest_q55` | 238 | 89 | 149 | 37.39 | 2.4803 | 1.4815 | 367.60 | 2.2878 | 1.3665 | 296.20 | 157.19 | 33.87 | -53.91 | 116.94 | False |

## Standalone Continuation Last Three Months

| Variant | Recent3 trades | Recent3 WR% | Recent3 W/L | Recent3 PF | Recent3 net | June trades | June WR% | June PF | June net |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `r2_break_retest_body45` | 152 | 42.76 | 2.3808 | 1.7788 | 635.58 | 90 | 53.33 | 2.3940 | 656.04 |
| `r2_impulse_retest_body45` | 84 | 53.57 | 2.2296 | 2.5726 | 669.87 | 61 | 60.66 | 3.1688 | 628.79 |
| `r2_impulse_retest_q55` | 47 | 57.45 | 2.1806 | 2.9438 | 437.13 | 34 | 67.65 | 3.9787 | 429.86 |

## Combined With Current R1 Plus Best R2 Pullback

| Book | Trades | WR% | W/L | PF | Net | Recent3 trades | Recent3 WR% | Recent3 PF | Recent3 net | Max DD | Dropped | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `current_r1_best_r2_pullback_plus_r2_break_retest_body45` | 1276 | 42.71 | 3.0988 | 2.3103 | 9692.76 | 156 | 44.23 | 1.9607 | 784.06 | 889.69 | 21 | False |
| `current_r1_best_r2_pullback_plus_r2_impulse_retest_body45` | 1060 | 44.72 | 3.0454 | 2.4634 | 9750.48 | 88 | 55.68 | 2.9212 | 818.35 | 889.69 | 15 | False |
| `current_r1_best_r2_pullback_plus_r2_impulse_retest_q55` | 848 | 46.93 | 2.8988 | 2.5638 | 9421.30 | 51 | 60.78 | 3.6041 | 585.61 | 889.69 | 11 | False |

## Yearly Table

| Book | Period | Trades | WR% | W/L | PF | Net |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `r2_break_retest_body45` | `2022` | 265 | 33.21 | 1.9610 | 0.9750 | -16.72 |
| `r2_break_retest_body45` | `2023` | 233 | 35.19 | 2.1075 | 1.1444 | 84.02 |
| `r2_break_retest_body45` | `2024` | 23 | 13.04 | 1.6858 | 0.2529 | -62.37 |
| `r2_break_retest_body45` | `2025` | 0 | 0.00 | 0.0000 | 0.0000 | 0.00 |
| `r2_break_retest_body45` | `2026` | 155 | 42.58 | 2.3470 | 1.7405 | 624.33 |
| `r2_impulse_retest_body45` | `2022` | 191 | 29.84 | 2.0875 | 0.8880 | -59.04 |
| `r2_impulse_retest_body45` | `2023` | 160 | 37.50 | 2.1708 | 1.3025 | 119.31 |
| `r2_impulse_retest_body45` | `2024` | 17 | 17.65 | 1.7032 | 0.3650 | -36.73 |
| `r2_impulse_retest_body45` | `2025` | 0 | 0.00 | 0.0000 | 0.0000 | 0.00 |
| `r2_impulse_retest_body45` | `2026` | 86 | 52.33 | 2.2043 | 2.4194 | 642.89 |
| `r2_impulse_retest_q55` | `2022` | 104 | 30.77 | 1.7436 | 0.7749 | -66.29 |
| `r2_impulse_retest_q55` | `2023` | 79 | 35.44 | 1.9470 | 1.0689 | 14.62 |
| `r2_impulse_retest_q55` | `2024` | 8 | 25.00 | 1.3230 | 0.4410 | -17.86 |
| `r2_impulse_retest_q55` | `2025` | 0 | 0.00 | 0.0000 | 0.0000 | 0.00 |
| `r2_impulse_retest_q55` | `2026` | 47 | 57.45 | 2.1806 | 2.9438 | 437.13 |
| `current_r1_best_r2_pullback_plus_r2_break_retest_body45` | `2022` | 337 | 37.39 | 2.7742 | 1.6566 | 640.40 |
| `current_r1_best_r2_pullback_plus_r2_break_retest_body45` | `2023` | 376 | 40.16 | 2.1895 | 1.4694 | 700.44 |
| `current_r1_best_r2_pullback_plus_r2_break_retest_body45` | `2024` | 194 | 43.81 | 3.0250 | 2.3590 | 2012.94 |
| `current_r1_best_r2_pullback_plus_r2_break_retest_body45` | `2025` | 186 | 54.30 | 1.9534 | 2.3211 | 3240.12 |
| `current_r1_best_r2_pullback_plus_r2_break_retest_body45` | `2026` | 183 | 44.81 | 5.0650 | 4.1121 | 3098.86 |
| `current_r1_best_r2_pullback_plus_r2_impulse_retest_body45` | `2022` | 264 | 35.98 | 3.0610 | 1.7207 | 599.85 |
| `current_r1_best_r2_pullback_plus_r2_impulse_retest_body45` | `2023` | 308 | 42.86 | 2.0972 | 1.5729 | 754.51 |
| `current_r1_best_r2_pullback_plus_r2_impulse_retest_body45` | `2024` | 188 | 45.21 | 2.9089 | 2.4005 | 2038.58 |
| `current_r1_best_r2_pullback_plus_r2_impulse_retest_body45` | `2025` | 186 | 54.30 | 1.9534 | 2.3211 | 3240.12 |
| `current_r1_best_r2_pullback_plus_r2_impulse_retest_body45` | `2026` | 114 | 53.51 | 5.3418 | 6.1481 | 3117.42 |
| `current_r1_best_r2_pullback_plus_r2_impulse_retest_q55` | `2022` | 179 | 38.55 | 3.0695 | 1.9254 | 569.75 |
| `current_r1_best_r2_pullback_plus_r2_impulse_retest_q55` | `2023` | 229 | 44.10 | 1.9973 | 1.5760 | 654.75 |
| `current_r1_best_r2_pullback_plus_r2_impulse_retest_q55` | `2024` | 179 | 46.93 | 2.7347 | 2.4181 | 2045.02 |
| `current_r1_best_r2_pullback_plus_r2_impulse_retest_q55` | `2025` | 186 | 54.30 | 1.9534 | 2.3211 | 3240.12 |
| `current_r1_best_r2_pullback_plus_r2_impulse_retest_q55` | `2026` | 75 | 57.33 | 6.4841 | 8.7130 | 2911.66 |

## Failed Checks

- `r2_break_retest_body45` standalone: wr_ge_50, pf_ge_1p50, top3_days_removed_net_gt_0
- `r2_impulse_retest_body45` standalone: wr_ge_50, pf_ge_1p50
- `r2_impulse_retest_q55` standalone: wr_ge_50, pf_ge_1p50, top3_days_removed_net_gt_0
- `current_r1_best_r2_pullback_plus_r2_break_retest_body45` combined: wr_ge_50
- `current_r1_best_r2_pullback_plus_r2_impulse_retest_body45` combined: wr_ge_50
- `current_r1_best_r2_pullback_plus_r2_impulse_retest_q55` combined: wr_ge_50

## Guard Summary

### `r2_break_retest_body45`
- `regime_router_block_short_r2_downtrend_only_state_chop`: 2361
- `regime_router_block_short_r2_downtrend_only_state_compression`: 635
- `regime_router_block_short_r2_downtrend_only_state_shock`: 945
- `regime_router_block_short_r2_downtrend_only_state_uptrend`: 1301
- `stop_ceiling_exceeded`: 24

### `r2_impulse_retest_body45`
- `regime_router_block_short_r2_downtrend_only_state_chop`: 1463
- `regime_router_block_short_r2_downtrend_only_state_compression`: 409
- `regime_router_block_short_r2_downtrend_only_state_shock`: 653
- `regime_router_block_short_r2_downtrend_only_state_uptrend`: 875
- `stop_ceiling_exceeded`: 20

### `r2_impulse_retest_q55`
- `regime_router_block_short_r2_downtrend_only_state_chop`: 724
- `regime_router_block_short_r2_downtrend_only_state_compression`: 208
- `regime_router_block_short_r2_downtrend_only_state_shock`: 326
- `regime_router_block_short_r2_downtrend_only_state_uptrend`: 461
- `stop_ceiling_exceeded`: 16

## Static Validation

- `variant_count_eq_3`: True
- `all_strict_r2_router`: True
- `all_short_only`: True
- `all_signal_15_or_19`: True
- `all_rr_2`: True
- `no_session_filter`: True
- `no_hour_day_filters`: True
- `no_breakeven_partial_trailing`: True

## Interpretation

At least one R2 continuation variant was profitable and recent-period safe, but no variant cleared both standalone and combined gates.

## Artifacts

- report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V1_EXACT_20260709.md`
- report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V1_EXACT_20260709.json`
- standalone_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V1_EXACT_20260709_STANDALONE.csv`
- combined_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V1_EXACT_20260709_COMBINED.csv`
- mt5_components_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V1_EXACT_20260709_MT5_COMPONENTS.md`
- mt5_components_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V1_EXACT_20260709_MT5_COMPONENTS.json`
- r2_break_retest_body45_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V1_EXACT_20260709_r2_break_retest_body45_NORMALIZED_TRADES.csv`
- r2_impulse_retest_body45_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V1_EXACT_20260709_r2_impulse_retest_body45_NORMALIZED_TRADES.csv`
- r2_impulse_retest_q55_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V1_EXACT_20260709_r2_impulse_retest_q55_NORMALIZED_TRADES.csv`
- current_r1_best_r2_pullback_plus_r2_break_retest_body45_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V1_EXACT_20260709_current_r1_best_r2_pullback_plus_r2_break_retest_body45_KEPT.csv`
- current_r1_best_r2_pullback_plus_r2_break_retest_body45_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V1_EXACT_20260709_current_r1_best_r2_pullback_plus_r2_break_retest_body45_DROPPED.csv`
- current_r1_best_r2_pullback_plus_r2_impulse_retest_body45_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V1_EXACT_20260709_current_r1_best_r2_pullback_plus_r2_impulse_retest_body45_KEPT.csv`
- current_r1_best_r2_pullback_plus_r2_impulse_retest_body45_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V1_EXACT_20260709_current_r1_best_r2_pullback_plus_r2_impulse_retest_body45_DROPPED.csv`
- current_r1_best_r2_pullback_plus_r2_impulse_retest_q55_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V1_EXACT_20260709_current_r1_best_r2_pullback_plus_r2_impulse_retest_q55_KEPT.csv`
- current_r1_best_r2_pullback_plus_r2_impulse_retest_q55_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V1_EXACT_20260709_current_r1_best_r2_pullback_plus_r2_impulse_retest_q55_DROPPED.csv`
