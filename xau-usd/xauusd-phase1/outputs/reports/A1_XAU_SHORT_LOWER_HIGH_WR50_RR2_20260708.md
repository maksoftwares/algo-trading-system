# A1 XAU Lower-High Short WR50 RR2 Exact MT5 Probe

Generated UTC: `2026-07-07T22:32:07Z`
Status: `NO_LOWER_HIGH_SHORT_WR50_RR2_SURVIVOR`

Scope: purpose-built lower-high failed-rally short signal, fixed RR2, exact MT5. No hour/session/day/month masks.

Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_SHORT_LOWER_HIGH_WR50_RR2_PREREG_2026_07_08.md`
Preregistration SHA256: `40ae338844ecf3aac66322b918037cb99f688682f3077edf76aa9e20e661a9e6`

## Results

| Variant | Trades | WR% | W/L | PF | Net | Stress PF | Stress net | 2023+2024 | Top10-removed | Top3-days-removed | Pos weeks% | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `lower_high_lh1_base` | 302 | 33.44 | 2.1168 | 1.0637 | 119.96 | 1.0151 | 29.36 | -14.75 | -281.76 | -176.97 | 45.76 | FAIL |
| `lower_high_lh2_deeper_drop` | 279 | 33.69 | 1.9995 | 1.0160 | 29.83 | 0.9720 | -53.87 | -32.86 | -373.50 | -210.51 | 45.76 | FAIL |
| `lower_high_lh3_tighter_reject` | 316 | 33.86 | 2.0307 | 1.0396 | 71.98 | 0.9879 | -22.82 | 58.47 | -327.49 | -126.31 | 50.85 | FAIL |

## Gate Failures

- `lower_high_lh1_base`: wr_ge_50, stress_pf_ge_1p15, y2023_2024_net_ge_0, top10_removed_net_gt_0, top3_days_removed_net_gt_0
- `lower_high_lh2_deeper_drop`: wr_ge_50, stress_net_gt_0, stress_pf_ge_1p15, y2023_2024_net_ge_0, top10_removed_net_gt_0, top3_days_removed_net_gt_0
- `lower_high_lh3_tighter_reject`: wr_ge_50, stress_net_gt_0, stress_pf_ge_1p15, top10_removed_net_gt_0, top3_days_removed_net_gt_0

## Decision

No lower-high variant reached the hard WR50/RR2 gate. Best WR was `lower_high_lh3_tighter_reject` at 33.86% with 316 trades. Best net was `lower_high_lh1_base` at 119.96 USD. The hard target remains unsolved.

## Artifacts

- md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_LOWER_HIGH_WR50_RR2_20260708.md`
- json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_LOWER_HIGH_WR50_RR2_20260708.json`
- summary_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_LOWER_HIGH_WR50_RR2_20260708_SUMMARY.csv`
- year_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_LOWER_HIGH_WR50_RR2_20260708_YEAR.csv`
- block_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_LOWER_HIGH_WR50_RR2_20260708_BLOCK.csv`
- mt5_components_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_LOWER_HIGH_WR50_RR2_20260708_MT5_COMPONENTS.md`
- mt5_components_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_LOWER_HIGH_WR50_RR2_20260708_MT5_COMPONENTS.json`
- lower_high_lh1_base_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_LOWER_HIGH_WR50_RR2_20260708_lower_high_lh1_base_NORMALIZED_TRADES.csv`
- lower_high_lh2_deeper_drop_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_LOWER_HIGH_WR50_RR2_20260708_lower_high_lh2_deeper_drop_NORMALIZED_TRADES.csv`
- lower_high_lh3_tighter_reject_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_LOWER_HIGH_WR50_RR2_20260708_lower_high_lh3_tighter_reject_NORMALIZED_TRADES.csv`
