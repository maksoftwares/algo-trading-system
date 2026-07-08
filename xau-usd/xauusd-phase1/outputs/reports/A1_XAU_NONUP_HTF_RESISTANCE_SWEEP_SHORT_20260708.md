# A1 XAU Non-Up HTF Resistance Sweep Short

Generated UTC: `2026-07-08T13:38:06Z`
Status: `NONUP_HTF_RESISTANCE_SWEEP_NO_SURVIVOR`

Scope: one fixed exact-MT5 short specialist test: D1 non-up, HTF resistance sweep/reclaim, fixed 2R. No hour/session/day/month masks.

Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_NONUP_HTF_RESISTANCE_SWEEP_SHORT_PREREG_2026_07_08.md`
Preregistration SHA256: `89c28c304ea0a626c3c770a074520de8f2607af424a726a1927642dffe7193ca`

## Result

| Variant | Trades | WR% | W/L | PF | Net | Stress PF | Stress net | Recent3 | 2023+2024 | Year+ | Top10-removed | Top3-days-removed | Pos weeks% | Watchlist | Strict |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `nonup_htf_resistance_sweep_short_v1` | 299 | 29.43 | 2.0257 | 0.8449 | -255.11 | 0.7981 | -344.81 | 135.72 | -271.34 | 3 | -635.83 | -405.50 | 41.00 | FAIL | FAIL |

## Gate Checks

- `trades_ge_100`: `PASS`
- `wr_ge_45`: `FAIL`
- `wl_ge_1p90`: `PASS`
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

## Interpretation

The fixed HTF resistance sweep short failed the preregistered watchlist gate. Do not tune this path without review.

## Artifacts

- report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_NONUP_HTF_RESISTANCE_SWEEP_SHORT_20260708.md`
- report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_NONUP_HTF_RESISTANCE_SWEEP_SHORT_20260708.json`
- summary_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_NONUP_HTF_RESISTANCE_SWEEP_SHORT_20260708_SUMMARY.csv`
- year_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_NONUP_HTF_RESISTANCE_SWEEP_SHORT_20260708_YEAR.csv`
- block_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_NONUP_HTF_RESISTANCE_SWEEP_SHORT_20260708_BLOCK.csv`
- normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_NONUP_HTF_RESISTANCE_SWEEP_SHORT_20260708_NORMALIZED_TRADES.csv`
- mt5_components_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_NONUP_HTF_RESISTANCE_SWEEP_SHORT_20260708_MT5_COMPONENTS.md`
- mt5_components_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_NONUP_HTF_RESISTANCE_SWEEP_SHORT_20260708_MT5_COMPONENTS.json`
