# A1 XAU Bear Quality-First Exact MT5 Probe

Generated UTC: `2026-07-07T13:33:04Z`
Status: `NO_BEAR_QUALITY_FIRST_HIT`
Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_BEAR_QUALITY_FIRST_PREREG_2026_07_07.md`
Preregistration SHA256: `e3ba07d4e3305f54bfecf53cc5e28a2b4451e421aa9a4eb8b56811e40859e1c6`

## Standalone Bear Quality Rows

| Variant | Trades | WR% | W/L | Active% | PF | Net | Stress W/L | Pos weeks% | Worst week | Recent3 | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `bear_quality_m5_ema_slope50` | 209 | 30.14 | 1.9311 | 12.56 | 0.8333 | -114.17 | 1.7549 | 40.35 | -29.13 | 0.00 | `QUALITY_REJECT` |
| `bear_quality_m5_ema_slope100` | 134 | 28.36 | 1.8855 | 8.72 | 0.7464 | -113.67 | 1.7113 | 29.17 | -17.80 | 0.00 | `QUALITY_REJECT` |
| `bear_quality_break_run_tight` | 192 | 27.60 | 2.0058 | 11.41 | 0.7648 | -145.26 | 1.8156 | 36.84 | -21.14 | 0.00 | `PAYOFF_OK_WR_FAIL` |
| `bear_quality_compression_break` | 0 | 0.00 | 0.0000 | 0.00 | 0.0000 | 0.00 | 0.0000 | 0.00 | 0.00 | 0.00 | `LOW_SAMPLE_REJECT` |
| `bear_quality_h4_pullback_d1bias` | 18 | 33.33 | 2.6756 | 1.44 | 1.3378 | 51.40 | 2.5907 | 42.86 | -24.34 | 0.00 | `PAYOFF_OK_WR_FAIL` |
| `bear_quality_weekly_rejection` | 8 | 12.50 | 1.7972 | 0.77 | 0.2567 | -49.91 | 1.7123 | 14.29 | -13.39 | 0.00 | `LOW_SAMPLE_REJECT` |

## Combined With Uptrend Baseline

| Combo | Signals | WR% | W/L | Active% | PF | Net | Stress W/L | Pos weeks% | Delta pp | Worst week | Recent3 | May | New kept | New net | Red touched | Red flipped | Red worsened | New red net | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `baseline_supportive_guard` | 3645 | 50.40 | 2.0895 | 85.71 | 2.1395 | 20701.41 | 1.9720 | 57.69 | 0.00 | -878.18 | 279.22 | -142.12 | 0 | 0.00 | 0 | 0 | 0 | 0.00 | `BASELINE` |
| `bear_quality_m5_ema_slope50_only` | 3830 | 49.37 | 2.1346 | 87.06 | 2.0969 | 20591.76 | 2.0119 | 56.25 | -1.44 | -878.18 | 279.22 | -142.12 | 186 | -99.17 | 30 | 2 | 18 | -85.63 | `REJECT_COMBINED_WR` |
| `bear_quality_m5_ema_slope100_only` | 3763 | 49.67 | 2.1225 | 86.77 | 2.1101 | 20596.25 | 2.0013 | 56.73 | -0.96 | -878.18 | 279.22 | -142.12 | 119 | -94.68 | 23 | 2 | 15 | -79.85 | `REJECT_COMBINED_WR` |
| `bear_quality_break_run_tight_only` | 3829 | 49.28 | 2.1415 | 86.86 | 2.0960 | 20559.86 | 2.0182 | 57.21 | -0.48 | -878.18 | 279.22 | -142.12 | 184 | -141.55 | 29 | 3 | 18 | -87.65 | `REJECT_COMBINED_WR` |
| `bear_quality_compression_break_only` | 3645 | 50.40 | 2.0895 | 85.71 | 2.1395 | 20701.41 | 1.9720 | 57.69 | 0.00 | -878.18 | 279.22 | -142.12 | 0 | 0.00 | 0 | 0 | 0 | 0.00 | `REJECT_COMBINED_WEEKLY_SHAPE` |
| `bear_quality_h4_pullback_d1bias_only` | 3663 | 50.31 | 2.0901 | 85.71 | 2.1329 | 20752.81 | 1.9729 | 57.21 | -0.48 | -878.18 | 279.22 | -142.12 | 18 | 51.40 | 6 | 3 | 3 | 33.51 | `REJECT_COMBINED_WEEKLY_SHAPE` |
| `bear_quality_weekly_rejection_only` | 3653 | 50.31 | 2.0897 | 85.81 | 2.1326 | 20651.50 | 1.9722 | 57.69 | 0.00 | -878.18 | 279.22 | -142.12 | 8 | -49.91 | 2 | 0 | 1 | -7.00 | `REJECT_COMBINED_WEEKLY_SHAPE` |
| `bear_quality_all_cells` | 4062 | 48.08 | 2.1870 | 87.15 | 2.0388 | 20422.41 | 2.0587 | 54.81 | -2.88 | -878.18 | 279.22 | -142.12 | 418 | -268.52 | 32 | 3 | 23 | -186.51 | `REJECT_COMBINED_WR` |

## Interpretation

No quality-first bear variant reached even the watchlist gate. Best WR row was `bear_quality_h4_pullback_d1bias`: 18 trades, WR 33.33%, W/L 2.6756, PF 1.3378, net 51.40 USD.

## Artifacts

- md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_BEAR_QUALITY_FIRST_EXACT_202207_202606.md`
- json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_BEAR_QUALITY_FIRST_EXACT_202207_202606.json`
- results_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_BEAR_QUALITY_FIRST_EXACT_202207_202606_RESULTS.csv`
- standalone_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_BEAR_QUALITY_FIRST_EXACT_202207_202606_STANDALONE.csv`
- mt5_components_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_BEAR_QUALITY_FIRST_EXACT_202207_202606_MT5_COMPONENTS.md`
- mt5_components_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_BEAR_QUALITY_FIRST_EXACT_202207_202606_MT5_COMPONENTS.json`
- bear_quality_m5_ema_slope50_only_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_BEAR_QUALITY_FIRST_EXACT_202207_202606_bear_quality_m5_ema_slope50_only_KEPT.csv`
- bear_quality_m5_ema_slope50_only_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_BEAR_QUALITY_FIRST_EXACT_202207_202606_bear_quality_m5_ema_slope50_only_DROPPED.csv`
- bear_quality_m5_ema_slope100_only_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_BEAR_QUALITY_FIRST_EXACT_202207_202606_bear_quality_m5_ema_slope100_only_KEPT.csv`
- bear_quality_m5_ema_slope100_only_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_BEAR_QUALITY_FIRST_EXACT_202207_202606_bear_quality_m5_ema_slope100_only_DROPPED.csv`
- bear_quality_break_run_tight_only_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_BEAR_QUALITY_FIRST_EXACT_202207_202606_bear_quality_break_run_tight_only_KEPT.csv`
- bear_quality_break_run_tight_only_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_BEAR_QUALITY_FIRST_EXACT_202207_202606_bear_quality_break_run_tight_only_DROPPED.csv`
- bear_quality_compression_break_only_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_BEAR_QUALITY_FIRST_EXACT_202207_202606_bear_quality_compression_break_only_KEPT.csv`
- bear_quality_compression_break_only_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_BEAR_QUALITY_FIRST_EXACT_202207_202606_bear_quality_compression_break_only_DROPPED.csv`
- bear_quality_h4_pullback_d1bias_only_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_BEAR_QUALITY_FIRST_EXACT_202207_202606_bear_quality_h4_pullback_d1bias_only_KEPT.csv`
- bear_quality_h4_pullback_d1bias_only_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_BEAR_QUALITY_FIRST_EXACT_202207_202606_bear_quality_h4_pullback_d1bias_only_DROPPED.csv`
- bear_quality_weekly_rejection_only_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_BEAR_QUALITY_FIRST_EXACT_202207_202606_bear_quality_weekly_rejection_only_KEPT.csv`
- bear_quality_weekly_rejection_only_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_BEAR_QUALITY_FIRST_EXACT_202207_202606_bear_quality_weekly_rejection_only_DROPPED.csv`
- bear_quality_all_cells_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_BEAR_QUALITY_FIRST_EXACT_202207_202606_bear_quality_all_cells_KEPT.csv`
- bear_quality_all_cells_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_BEAR_QUALITY_FIRST_EXACT_202207_202606_bear_quality_all_cells_DROPPED.csv`
