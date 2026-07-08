# A1 XAU R4 Chop Failed-Break V1 Exact-MT5

Generated UTC: `2026-07-08T17:48:09Z`
Status: `R4_CHOP_FAILED_BREAK_V1_NO_SURVIVOR`

Scope: exact-MT5 run using the EA-side R4 chop-only router. Research-only.

Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_R4_CHOP_FAILED_BREAK_V1_EXACT_PREREG_2026_07_08.md`
Preregistration SHA256: `17b01c91b1e3ddd73b4f3eed7d6f25c8ad2e53512edd531d08a35b790bf70416`

## Results

| Book | Trades | WR% | W/L | PF | Net | Stress W/L | Stress PF | Recent3 trades | Recent3 net | Max DD | Top10 rem | Top3 days rem | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `r4_chop_failed_break_v1_sweep_reclaim` | 1610 | 31.99 | 2.0965 | 0.9860 | -93.48 | 1.9516 | 0.9179 | 135 | 98.84 | 313.39 | -553.91 | -358.25 | False |
| `current_r1_plus_r4_chop_failed_break_v1_sweep_reclaim` | 2168 | 36.67 | 2.9943 | 1.7338 | 8622.88 | 2.8590 | 1.6554 | 135 | 98.84 | 912.41 | 5714.23 | 6258.58 | False |

## Current R1 Baseline

Current R1 book: 558 trades, WR 50.18%, W/L 2.7028, PF 2.7223, net 8716.36, recent3 trades 0, recent3 net 0.00, max DD 889.69.

## Failed Checks

- `r4_chop_failed_break_v1_sweep_reclaim`: wr_ge_50, pf_ge_1p50, stress_pf_ge_1p30, net_gt_0, net_2023_2024_ge_0, top10_removed_net_gt_0, top3_days_removed_net_gt_0
- `current_r1_plus_r4_chop_failed_break_v1_sweep_reclaim`: net_gt_current_r1, wr_ge_50, pf_ge_2

## Router / Guard Notes

- `estimated_cost_r_too_high`: 2
- `regime_router_block_r4_chop_only_state_compression`: 411
- `regime_router_block_r4_chop_only_state_downtrend`: 420
- `regime_router_block_r4_chop_only_state_shock`: 651
- `regime_router_block_r4_chop_only_state_uptrend`: 951
- `spread_too_high`: 3
- `stop_ceiling_exceeded`: 45

## Interpretation

The chop failed-break test did not produce a positive standalone or useful combined recent-coverage result.

## Artifacts

- report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_FAILED_BREAK_V1_EXACT_20260708.md`
- report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_FAILED_BREAK_V1_EXACT_20260708.json`
- standalone_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_FAILED_BREAK_V1_EXACT_20260708_STANDALONE.csv`
- combined_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_FAILED_BREAK_V1_EXACT_20260708_COMBINED.csv`
- normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_FAILED_BREAK_V1_EXACT_20260708_r4_chop_failed_break_v1_sweep_reclaim_NORMALIZED_TRADES.csv`
- combined_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_FAILED_BREAK_V1_EXACT_20260708_current_r1_plus_r4_chop_failed_break_v1_sweep_reclaim_KEPT.csv`
- combined_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_FAILED_BREAK_V1_EXACT_20260708_current_r1_plus_r4_chop_failed_break_v1_sweep_reclaim_DROPPED.csv`
- mt5_report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_FAILED_BREAK_V1_EXACT_20260708_MT5.md`
- mt5_report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_FAILED_BREAK_V1_EXACT_20260708_MT5.json`
