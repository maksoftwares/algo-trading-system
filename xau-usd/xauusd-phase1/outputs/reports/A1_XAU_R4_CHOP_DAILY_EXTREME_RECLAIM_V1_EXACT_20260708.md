# A1 XAU R4 Chop Daily-Extreme Reclaim V1 Exact-MT5

Generated UTC: `2026-07-08T17:51:38Z`
Status: `R4_CHOP_DAILY_EXTREME_RECLAIM_V1_NO_SURVIVOR`

Scope: exact-MT5 run using the EA-side R4 chop-only router. Research-only.

Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_R4_CHOP_DAILY_EXTREME_RECLAIM_V1_EXACT_PREREG_2026_07_08.md`
Preregistration SHA256: `d65eff2675f73252ab648b7e71b87d9d5d48b1794dc7849bf4264529d8167987`

## Results

| Book | Trades | WR% | W/L | PF | Net | Stress W/L | Stress PF | Recent3 trades | Recent3 net | Max DD | Top10 rem | Top3 days rem | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `r4_chop_daily_extreme_reclaim_v1_liquid` | 200 | 33.50 | 1.5553 | 0.7835 | -311.76 | 1.4864 | 0.7488 | 13 | -26.63 | 481.29 | -730.88 | -509.43 | False |
| `current_r1_plus_r4_chop_daily_extreme_reclaim_v1_liquid` | 758 | 45.78 | 2.7157 | 2.2928 | 8404.60 | 2.6465 | 2.2344 | 13 | -26.63 | 973.39 | 5495.95 | 6040.30 | False |

## Current R1 Baseline

Current R1 book: 558 trades, WR 50.18%, W/L 2.7028, PF 2.7223, net 8716.36, recent3 trades 0, recent3 net 0.00, max DD 889.69.

## Failed Checks

- `r4_chop_daily_extreme_reclaim_v1_liquid`: wr_ge_50, wl_ge_1p80, pf_ge_1p50, stress_pf_ge_1p30, stress_wl_ge_1p65, net_gt_0, recent3_trades_ge_30, recent3_net_gt_0, top10_removed_net_gt_0, top3_days_removed_net_gt_0
- `current_r1_plus_r4_chop_daily_extreme_reclaim_v1_liquid`: net_gt_current_r1, recent3_net_ge_0, wr_ge_50

## Router / Guard Notes

- `regime_router_block_r4_chop_only_state_compression`: 62
- `regime_router_block_r4_chop_only_state_downtrend`: 64
- `regime_router_block_r4_chop_only_state_shock`: 182
- `regime_router_block_r4_chop_only_state_uptrend`: 174

## Interpretation

The daily-extreme R4 test did not produce a positive standalone or useful combined recent-coverage result.

## Artifacts

- report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_DAILY_EXTREME_RECLAIM_V1_EXACT_20260708.md`
- report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_DAILY_EXTREME_RECLAIM_V1_EXACT_20260708.json`
- standalone_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_DAILY_EXTREME_RECLAIM_V1_EXACT_20260708_STANDALONE.csv`
- combined_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_DAILY_EXTREME_RECLAIM_V1_EXACT_20260708_COMBINED.csv`
- normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_DAILY_EXTREME_RECLAIM_V1_EXACT_20260708_r4_chop_daily_extreme_reclaim_v1_liquid_NORMALIZED_TRADES.csv`
- combined_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_DAILY_EXTREME_RECLAIM_V1_EXACT_20260708_current_r1_plus_r4_chop_daily_extreme_reclaim_v1_liquid_KEPT.csv`
- combined_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_DAILY_EXTREME_RECLAIM_V1_EXACT_20260708_current_r1_plus_r4_chop_daily_extreme_reclaim_v1_liquid_DROPPED.csv`
- mt5_report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_DAILY_EXTREME_RECLAIM_V1_EXACT_20260708_MT5.md`
- mt5_report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_DAILY_EXTREME_RECLAIM_V1_EXACT_20260708_MT5.json`
