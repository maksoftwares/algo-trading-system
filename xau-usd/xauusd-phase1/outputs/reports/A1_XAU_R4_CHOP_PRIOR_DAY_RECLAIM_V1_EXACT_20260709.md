# A1 XAU R4 Chop Prior-Day Reclaim V1 Exact-MT5

Generated UTC: `2026-07-09T06:49:08Z`
Status: `R4_CHOP_PRIOR_DAY_RECLAIM_V1_SHADOW_ONLY`

Scope: exact-MT5 run using the EA-side R4 chop-only router and prior-day level reversal signal. Research-only.

Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_PREREG_2026_07_09.md`
Preregistration SHA256: `1a253a72a7a40e6511299058097f36768b50168c7cde99fdc37fe358ac0e94a4`

## Standalone Results

| Variant | Trades | WR% | W/L | PF | Net | Stress W/L | Stress PF | Recent3 trades | Recent3 net | Max DD | Top10 rem | Top3 days rem | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `r4_chop_prior_day_reclaim_v1_both` | 526 | 33.84 | 2.0740 | 1.0608 | 95.06 | 1.8815 | 0.9624 | 24 | -26.73 | 134.56 | -188.67 | -38.69 | False |
| `r4_chop_prior_day_reclaim_v1_long` | 278 | 35.25 | 2.0071 | 1.0928 | 73.93 | 1.8163 | 0.9889 | 7 | -52.30 | 110.85 | -162.22 | -48.84 | False |
| `r4_chop_prior_day_reclaim_v1_short` | 274 | 30.66 | 2.2139 | 0.9788 | -17.53 | 2.0066 | 0.8871 | 17 | 25.57 | 90.03 | -256.09 | -125.13 | False |

## Combined With Current R1

| Book | Trades | WR% | W/L | PF | Net | Stress W/L | Stress PF | Recent3 trades | Recent3 net | Max DD | Top10 rem | Top3 days rem | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `current_r1_plus_r4_chop_prior_day_reclaim_v1_both` | 1084 | 42.25 | 3.1851 | 2.3303 | 8811.42 | 3.0697 | 2.2459 | 24 | -26.73 | 880.88 | 5902.77 | 6447.12 | False |
| `current_r1_plus_r4_chop_prior_day_reclaim_v1_long` | 836 | 45.22 | 3.0298 | 2.5006 | 8790.29 | 2.9375 | 2.4244 | 7 | -52.30 | 879.18 | 5881.64 | 6425.99 | False |
| `current_r1_plus_r4_chop_prior_day_reclaim_v1_short` | 832 | 43.75 | 3.1853 | 2.4775 | 8698.83 | 3.0878 | 2.4016 | 17 | 25.57 | 896.56 | 5790.18 | 6334.53 | False |

## Current R1 Baseline

Current R1 book: 558 trades, WR 50.18%, W/L 2.7028, PF 2.7223, net 8716.36, recent3 trades 0, recent3 net 0.00, max DD 889.69.

## Failed Checks

- `r4_chop_prior_day_reclaim_v1_both`: wr_ge_50, pf_ge_1p50, stress_pf_ge_1p30, recent3_trades_ge_30, recent3_net_gt_0, top10_removed_net_gt_0, top3_days_removed_net_gt_0
- `r4_chop_prior_day_reclaim_v1_long`: wr_ge_50, pf_ge_1p50, stress_pf_ge_1p30, recent3_trades_ge_30, recent3_net_gt_0, top10_removed_net_gt_0, top3_days_removed_net_gt_0
- `r4_chop_prior_day_reclaim_v1_short`: wr_ge_50, pf_ge_1p50, stress_pf_ge_1p30, net_gt_0, recent3_trades_ge_30, net_2023_2024_ge_0, top10_removed_net_gt_0, top3_days_removed_net_gt_0
- `current_r1_plus_r4_chop_prior_day_reclaim_v1_both`: recent3_net_ge_0, wr_ge_50
- `current_r1_plus_r4_chop_prior_day_reclaim_v1_long`: recent3_net_ge_0, wr_ge_50
- `current_r1_plus_r4_chop_prior_day_reclaim_v1_short`: net_gt_current_r1, wr_ge_50

## Router / Guard Notes

### `r4_chop_prior_day_reclaim_v1_both`
- `estimated_cost_r_too_high`: 77
- `regime_router_block_r4_chop_only_state_compression`: 317
- `regime_router_block_r4_chop_only_state_downtrend`: 200
- `regime_router_block_r4_chop_only_state_shock`: 430
- `regime_router_block_r4_chop_only_state_uptrend`: 462
- `stop_ceiling_exceeded`: 30
### `r4_chop_prior_day_reclaim_v1_long`
- `estimated_cost_r_too_high`: 36
- `regime_router_block_r4_chop_only_state_compression`: 136
- `regime_router_block_r4_chop_only_state_downtrend`: 154
- `regime_router_block_r4_chop_only_state_shock`: 210
- `regime_router_block_r4_chop_only_state_uptrend`: 129
- `stop_ceiling_exceeded`: 15
### `r4_chop_prior_day_reclaim_v1_short`
- `estimated_cost_r_too_high`: 41
- `regime_router_block_r4_chop_only_state_compression`: 181
- `regime_router_block_r4_chop_only_state_downtrend`: 46
- `regime_router_block_r4_chop_only_state_shock`: 220
- `regime_router_block_r4_chop_only_state_uptrend`: 333
- `stop_ceiling_exceeded`: 15

## Interpretation

The R4 prior-day reclaim pass produced useful evidence but did not clear every promotion gate. Do not deploy without repair/review.

## Artifacts

- report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_20260709.md`
- report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_20260709.json`
- standalone_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_20260709_STANDALONE.csv`
- combined_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_20260709_COMBINED.csv`
- mt5_report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_20260709_MT5.md`
- mt5_report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_20260709_MT5.json`
- r4_chop_prior_day_reclaim_v1_both_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_20260709_r4_chop_prior_day_reclaim_v1_both_NORMALIZED_TRADES.csv`
- r4_chop_prior_day_reclaim_v1_both_combined_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_20260709_current_r1_plus_r4_chop_prior_day_reclaim_v1_both_KEPT.csv`
- r4_chop_prior_day_reclaim_v1_both_combined_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_20260709_current_r1_plus_r4_chop_prior_day_reclaim_v1_both_DROPPED.csv`
- r4_chop_prior_day_reclaim_v1_long_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_20260709_r4_chop_prior_day_reclaim_v1_long_NORMALIZED_TRADES.csv`
- r4_chop_prior_day_reclaim_v1_long_combined_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_20260709_current_r1_plus_r4_chop_prior_day_reclaim_v1_long_KEPT.csv`
- r4_chop_prior_day_reclaim_v1_long_combined_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_20260709_current_r1_plus_r4_chop_prior_day_reclaim_v1_long_DROPPED.csv`
- r4_chop_prior_day_reclaim_v1_short_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_20260709_r4_chop_prior_day_reclaim_v1_short_NORMALIZED_TRADES.csv`
- r4_chop_prior_day_reclaim_v1_short_combined_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_20260709_current_r1_plus_r4_chop_prior_day_reclaim_v1_short_KEPT.csv`
- r4_chop_prior_day_reclaim_v1_short_combined_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_20260709_current_r1_plus_r4_chop_prior_day_reclaim_v1_short_DROPPED.csv`
