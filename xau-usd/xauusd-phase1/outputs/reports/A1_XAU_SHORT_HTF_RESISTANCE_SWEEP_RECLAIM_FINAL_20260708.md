# A1 XAU Short HTF Resistance Sweep/Reclaim Final Test

Generated UTC: `2026-07-08T06:42:47Z`
Status: `WR50_FINAL_FALSIFIED_CLOSE_STANDALONE_SHORT_SEARCH`

Scope: one fixed exact-MT5 final falsification test for standalone XAU short WR50/RR2. Signal is evaluated once per completed M15 bar. No hour/session/day/month masks, no RR reduction.

Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_SHORT_HTF_RESISTANCE_SWEEP_RECLAIM_PREREG_2026_07_08.md`
Preregistration SHA256: `337bcc8a8d527798b94ccfb7e88fe43426599cf9424ca40f61753129dbc8b386`

## Result

| Variant | Trades | WR% | W/L | PF | Net | Stress PF | Stress net | 2023+2024 | Year buckets+ | Top10-removed | Top3-days-removed | Pos weeks% | True pass | Watchlist |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `short_htf_resistance_sweep_reclaim_rr2` | 299 | 29.43 | 2.0257 | 0.8449 | -255.11 | 0.7981 | -344.81 | -271.34 | 3 | -635.83 | -405.50 | 41.00 | FAIL | FAIL |

## Gate Checks

- `wr_ge_50`: `FAIL`
- `wr_ge_45_watchlist`: `FAIL`
- `wl_ge_1p90`: `PASS`
- `trades_ge_100`: `PASS`
- `pf_ge_1p20`: `FAIL`
- `stress_pf_ge_1p15`: `FAIL`
- `stress_net_gt_0`: `FAIL`
- `y2023_2024_net_ge_0`: `FAIL`
- `positive_year_buckets_ge_3`: `PASS`
- `top10_removed_net_gt_0`: `FAIL`
- `top3_days_removed_net_gt_0`: `FAIL`

## By Year

| Year | Trades | WR% | W/L | PF | Net |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2022 | 57 | 35.09 | 2.3827 | 1.2880 | 54.87 |
| 2023 | 81 | 33.33 | 2.0553 | 1.0277 | 7.56 |
| 2024 | 69 | 18.84 | 1.5010 | 0.3484 | -278.90 |
| 2025 | 58 | 29.31 | 2.1482 | 0.8907 | -41.99 |
| 2026 | 34 | 32.35 | 2.1099 | 1.0091 | 3.35 |

## Decision

The final HTF resistance sweep test landed below the 45% WR falsification threshold. Per both reviews, close the standalone XAU short WR50/RR2 search. Treat shorts as hedge-only unless a new reviewer-signed objective is created.

## Artifacts

- md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_HTF_RESISTANCE_SWEEP_RECLAIM_FINAL_20260708.md`
- json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_HTF_RESISTANCE_SWEEP_RECLAIM_FINAL_20260708.json`
- summary_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_HTF_RESISTANCE_SWEEP_RECLAIM_FINAL_20260708_SUMMARY.csv`
- year_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_HTF_RESISTANCE_SWEEP_RECLAIM_FINAL_20260708_YEAR.csv`
- block_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_HTF_RESISTANCE_SWEEP_RECLAIM_FINAL_20260708_BLOCK.csv`
- normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_HTF_RESISTANCE_SWEEP_RECLAIM_FINAL_20260708_short_htf_resistance_sweep_reclaim_rr2_NORMALIZED_TRADES.csv`
- mt5_components_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_HTF_RESISTANCE_SWEEP_RECLAIM_FINAL_20260708_MT5_COMPONENTS.md`
- mt5_components_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_HTF_RESISTANCE_SWEEP_RECLAIM_FINAL_20260708_MT5_COMPONENTS.json`
