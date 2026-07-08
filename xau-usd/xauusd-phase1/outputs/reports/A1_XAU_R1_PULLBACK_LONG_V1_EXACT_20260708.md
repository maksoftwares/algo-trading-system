# A1 XAU R1 Pullback Long V1 Exact-MT5

Generated UTC: `2026-07-08T16:19:28Z`
Status: `R1_PULLBACK_LONG_V1_SHADOW_ONLY`

Scope: exact-MT5 component rerun using the EA-side R1 router. This remains research-only; no demo/live runtime state was changed.

Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_R1_PULLBACK_LONG_V1_EXACT_PREREG_2026_07_08.md`
Preregistration SHA256: `b8657c61e4454a219b5d1bfc861a785ba072189b610aaad11122ba0e3e84d484`
Routed R1 box baseline: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_REGIME_ROUTER_V1_EXACT_20260708_router_v1_r1_long_box2_prevhealth_NORMALIZED_TRADES.csv`
Routed R1 box baseline SHA256: `ad50b1608753b0eb333205958ac147796e8972e8a44b0e4b817530ffee1ae148`

## Standalone Pullback Results

| Variant | Trades | WR% | W/L | PF | Net | Stress W/L | Stress PF | Active% | Max DD | +Years | Q2 trades | Q2 net | Top10 rem | Top3 days rem | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `r1_pullback_long_v1_m5_confirm` | 0 | 0.00 | 0.0000 | 0.0000 | 0.00 | 0.0000 | 0.0000 | 0.00 | 0.00 | 0 | 0 | 0.00 | 0.00 | 0.00 | False |
| `r1_pullback_long_v1_m15_confirm` | 1178 | 40.83 | 2.1631 | 1.4928 | 2641.87 | 2.0444 | 1.4108 | 22.15 | 399.46 | 3 | 0 | 0.00 | 2219.10 | 2045.65 | False |

## Combined With Routed R1 Box

| Book | Trades | WR% | W/L | PF | Net | Stress W/L | Stress PF | Active% | Max DD | +Months | -Months | Best month share% | Dropped | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `box_plus_r1_pullback_long_v1_m5_confirm` | 145 | 59.31 | 2.1804 | 3.1782 | 7050.42 | 2.1631 | 3.1530 | 7.96 | 866.37 | 15 | 10 | 37.91 | 0 | False |
| `box_plus_r1_pullback_long_v1_m15_confirm` | 1322 | 42.81 | 2.8329 | 2.1210 | 9638.23 | 2.7344 | 2.0472 | 23.11 | 958.10 | 18 | 18 | 29.15 | 1 | False |

## Baseline

Routed R1 box baseline: 145 trades, WR 59.31%, W/L 2.1804, PF 3.1782, net 7050.42, active 7.96%, max DD 866.37.

## Failed Checks

- `r1_pullback_long_v1_m5_confirm`: trades_ge_150, wr_ge_50, wl_ge_1p90, pf_ge_1p50, stress_pf_ge_1p30, stress_wl_ge_1p80, net_gt_0, positive_year_buckets_ge_3, top10_removed_net_gt_0, top3_days_removed_net_gt_0
- `r1_pullback_long_v1_m15_confirm`: wr_ge_50, pf_ge_1p50
- `box_plus_r1_pullback_long_v1_m5_confirm`: net_gt_box_baseline, active_plus_5pp, best_month_share_lte_30pct
- `box_plus_r1_pullback_long_v1_m15_confirm`: dd_not_worse_10pct

## Router / Guard Notes

### `r1_pullback_long_v1_m5_confirm`
- no router blocks logged

### `r1_pullback_long_v1_m15_confirm`
- `regime_router_block_long_r1_uptrend_only_state_chop`: 914
- `regime_router_block_long_r1_uptrend_only_state_compression`: 362
- `regime_router_block_long_r1_uptrend_only_state_downtrend`: 37
- `regime_router_block_long_r1_uptrend_only_state_shock`: 637

## Interpretation

A pullback variant was positive, but none passed the combined-with-box gate. Do not add it to the deployable R1 book without another preregistered repair.

## Artifacts

- report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_PULLBACK_LONG_V1_EXACT_20260708.md`
- report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_PULLBACK_LONG_V1_EXACT_20260708.json`
- standalone_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_PULLBACK_LONG_V1_EXACT_20260708_STANDALONE.csv`
- combined_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_PULLBACK_LONG_V1_EXACT_20260708_COMBINED.csv`
- mt5_components_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_PULLBACK_LONG_V1_EXACT_20260708_MT5_COMPONENTS.md`
- mt5_components_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_PULLBACK_LONG_V1_EXACT_20260708_MT5_COMPONENTS.json`
- r1_pullback_long_v1_m5_confirm_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_PULLBACK_LONG_V1_EXACT_20260708_r1_pullback_long_v1_m5_confirm_NORMALIZED_TRADES.csv`
- r1_pullback_long_v1_m15_confirm_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_PULLBACK_LONG_V1_EXACT_20260708_r1_pullback_long_v1_m15_confirm_NORMALIZED_TRADES.csv`
- box_plus_r1_pullback_long_v1_m5_confirm_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_PULLBACK_LONG_V1_EXACT_20260708_box_plus_r1_pullback_long_v1_m5_confirm_KEPT.csv`
- box_plus_r1_pullback_long_v1_m5_confirm_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_PULLBACK_LONG_V1_EXACT_20260708_box_plus_r1_pullback_long_v1_m5_confirm_DROPPED.csv`
- box_plus_r1_pullback_long_v1_m15_confirm_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_PULLBACK_LONG_V1_EXACT_20260708_box_plus_r1_pullback_long_v1_m15_confirm_KEPT.csv`
- box_plus_r1_pullback_long_v1_m15_confirm_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_PULLBACK_LONG_V1_EXACT_20260708_box_plus_r1_pullback_long_v1_m15_confirm_DROPPED.csv`
