# A1 XAU R4 Chop Opening-Range Reversal V1 Exact-MT5

Generated UTC: `2026-07-09T07:49:05Z`
Status: `R4_CHOP_ORREV_V1_SHADOW_ONLY`

Scope: exact-MT5 run using the EA-side R4 chop-only router and opening-range reversal signal. Research-only.

Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_R4_CHOP_OPENING_RANGE_REVERSAL_V1_EXACT_PREREG_2026_07_09.md`
Preregistration SHA256: `e5cd691d43471e249310426886b4bc5e51759cc45504064dd707da68b4b8e09b`

## Current R1+R2 Baseline

Current R1+R2 book: 678 trades, WR 51.03%, W/L 2.6082, PF 2.7182, net 9640.05, recent3 trades 59, recent3 net 764.92, max DD 889.69.

## Standalone R4 Results

| Variant | Trades | WR% | W/L | PF | Net | Stress W/L | Stress PF | Recent3 trades | Recent3 net | Max DD | Top10 rem | Top3 days rem | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `r4_chop_orrev_london_firm_both` | 578 | 33.22 | 2.1668 | 1.0778 | 125.16 | 1.9542 | 0.9720 | 46 | 43.08 | 119.44 | -111.15 | 16.26 | False |
| `r4_chop_orrev_london_firm_long` | 286 | 34.62 | 2.0512 | 1.0859 | 70.89 | 1.8569 | 0.9831 | 22 | 12.59 | 105.11 | -140.47 | 3.13 | False |
| `r4_chop_orrev_london_firm_short` | 336 | 32.14 | 2.2741 | 1.0772 | 71.31 | 2.0483 | 0.9703 | 27 | 26.39 | 119.31 | -162.17 | -27.73 | False |

## Combined With Current R1+R2

| Book | Trades | WR% | W/L | PF | Net | Stress W/L | Stress PF | Recent3 trades | Recent3 net | Max DD | Top10 rem | Top3 days rem | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `current_r1_r2_plus_r4_chop_orrev_london_firm_both` | 1256 | 42.83 | 3.1398 | 2.3527 | 9765.21 | 3.0198 | 2.2628 | 105 | 808.00 | 846.66 | 6856.56 | 7400.91 | False |
| `current_r1_r2_plus_r4_chop_orrev_london_firm_long` | 964 | 46.16 | 2.9261 | 2.5089 | 9710.94 | 2.8334 | 2.4294 | 81 | 777.51 | 901.92 | 6802.29 | 7346.64 | False |
| `current_r1_r2_plus_r4_chop_orrev_london_firm_short` | 1014 | 44.77 | 3.0668 | 2.4863 | 9711.36 | 2.9648 | 2.4036 | 86 | 791.31 | 851.89 | 6802.71 | 7347.06 | False |

## Failed Checks

- `r4_chop_orrev_london_firm_both`: wr_ge_45, pf_ge_1p30, stress_pf_ge_1p15, net_2023_2024_ge_0, top10_removed_net_gt_0
- `r4_chop_orrev_london_firm_long`: wr_ge_45, pf_ge_1p30, stress_pf_ge_1p15, top10_removed_net_gt_0
- `r4_chop_orrev_london_firm_short`: wr_ge_45, pf_ge_1p30, stress_pf_ge_1p15, net_2023_2024_ge_0, top10_removed_net_gt_0, top3_days_removed_net_gt_0
- `current_r1_r2_plus_r4_chop_orrev_london_firm_both`: wr_ge_50
- `current_r1_r2_plus_r4_chop_orrev_london_firm_long`: wr_ge_50
- `current_r1_r2_plus_r4_chop_orrev_london_firm_short`: wr_ge_50

## Router / Guard Notes

### `r4_chop_orrev_london_firm_both`
- `estimated_cost_r_too_high`: 129
- `regime_router_block_r4_chop_only_state_compression`: 266
- `regime_router_block_r4_chop_only_state_downtrend`: 300
- `regime_router_block_r4_chop_only_state_shock`: 397
- `regime_router_block_r4_chop_only_state_uptrend`: 621
- `spread_too_high`: 2
- `stop_ceiling_exceeded`: 11

### `r4_chop_orrev_london_firm_long`
- `estimated_cost_r_too_high`: 75
- `regime_router_block_r4_chop_only_state_compression`: 141
- `regime_router_block_r4_chop_only_state_downtrend`: 138
- `regime_router_block_r4_chop_only_state_shock`: 175
- `regime_router_block_r4_chop_only_state_uptrend`: 281
- `spread_too_high`: 2
- `stop_ceiling_exceeded`: 5

### `r4_chop_orrev_london_firm_short`
- `estimated_cost_r_too_high`: 54
- `regime_router_block_r4_chop_only_state_compression`: 125
- `regime_router_block_r4_chop_only_state_downtrend`: 162
- `regime_router_block_r4_chop_only_state_shock`: 222
- `regime_router_block_r4_chop_only_state_uptrend`: 340
- `stop_ceiling_exceeded`: 6

## Interpretation

At least one variant added recent-three-month value but did not clear the full standalone and combined promotion checks.

## Artifacts

- report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_OPENING_RANGE_REVERSAL_V1_EXACT_20260709.md`
- report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_OPENING_RANGE_REVERSAL_V1_EXACT_20260709.json`
- standalone_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_OPENING_RANGE_REVERSAL_V1_EXACT_20260709_STANDALONE.csv`
- combined_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_OPENING_RANGE_REVERSAL_V1_EXACT_20260709_COMBINED.csv`
- mt5_report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_OPENING_RANGE_REVERSAL_V1_EXACT_20260709_MT5.md`
- mt5_report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_OPENING_RANGE_REVERSAL_V1_EXACT_20260709_MT5.json`
- r4_chop_orrev_london_firm_both_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_OPENING_RANGE_REVERSAL_V1_EXACT_20260709_r4_chop_orrev_london_firm_both_NORMALIZED_TRADES.csv`
- r4_chop_orrev_london_firm_both_combined_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_OPENING_RANGE_REVERSAL_V1_EXACT_20260709_current_r1_r2_plus_r4_chop_orrev_london_firm_both_KEPT.csv`
- r4_chop_orrev_london_firm_both_combined_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_OPENING_RANGE_REVERSAL_V1_EXACT_20260709_current_r1_r2_plus_r4_chop_orrev_london_firm_both_DROPPED.csv`
- r4_chop_orrev_london_firm_long_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_OPENING_RANGE_REVERSAL_V1_EXACT_20260709_r4_chop_orrev_london_firm_long_NORMALIZED_TRADES.csv`
- r4_chop_orrev_london_firm_long_combined_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_OPENING_RANGE_REVERSAL_V1_EXACT_20260709_current_r1_r2_plus_r4_chop_orrev_london_firm_long_KEPT.csv`
- r4_chop_orrev_london_firm_long_combined_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_OPENING_RANGE_REVERSAL_V1_EXACT_20260709_current_r1_r2_plus_r4_chop_orrev_london_firm_long_DROPPED.csv`
- r4_chop_orrev_london_firm_short_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_OPENING_RANGE_REVERSAL_V1_EXACT_20260709_r4_chop_orrev_london_firm_short_NORMALIZED_TRADES.csv`
- r4_chop_orrev_london_firm_short_combined_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_OPENING_RANGE_REVERSAL_V1_EXACT_20260709_current_r1_r2_plus_r4_chop_orrev_london_firm_short_KEPT.csv`
- r4_chop_orrev_london_firm_short_combined_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_OPENING_RANGE_REVERSAL_V1_EXACT_20260709_current_r1_r2_plus_r4_chop_orrev_london_firm_short_DROPPED.csv`
