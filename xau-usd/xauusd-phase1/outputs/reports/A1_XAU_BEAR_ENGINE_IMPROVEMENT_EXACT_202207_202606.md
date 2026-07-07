# A1 XAU Bear Engine Improvement Exact MT5 Probe

Generated UTC: `2026-07-07T13:12:46Z`
Status: `NO_BEAR_ENGINE_IMPROVEMENT`
Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_BEAR_ENGINE_IMPROVEMENT_PREREG_2026_07_07.md`
Preregistration SHA256: `e54abb919d743b9742f5399b99aec1adc16fcf5b80304c342ea7fc14a257e2f5`

## Standalone Bear Rows

| Variant | Trades | WR% | W/L | Active% | PF | Net | Stress W/L | Pos weeks% | Recent3 | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `bear_m5_ema_h1_only_rr2_morefreq` | 438 | 33.11 | 2.1599 | 19.18 | 1.0689 | 139.24 | 2.0282 | 41.77 | 286.25 | `NO_BEAR_IMPROVEMENT` |
| `bear_m5_ema_h1h4_rr2_strict_body` | 432 | 31.71 | 2.1173 | 18.89 | 0.9833 | -32.25 | 1.9806 | 36.36 | 158.44 | `NO_BEAR_IMPROVEMENT` |
| `bear_m5_ema_h1h4_rr2_fast_slope` | 406 | 33.00 | 2.1388 | 18.22 | 1.0537 | 98.80 | 2.0056 | 39.47 | 181.56 | `NO_BEAR_IMPROVEMENT` |
| `bear_ema_pullback_h1h4_rr2` | 487 | 31.42 | 2.0018 | 19.18 | 0.9170 | -186.96 | 1.8739 | 35.00 | 115.62 | `MORE_TRADES_BUT_WR_NOT_UP` |
| `bear_break_run_h1h4_rr2` | 445 | 32.13 | 2.3536 | 17.55 | 1.1144 | 208.00 | 2.1943 | 38.67 | 182.17 | `MORE_TRADES_BUT_WR_NOT_UP` |

## Combined With Uptrend Baseline

| Combo | Signals | WR% | W/L | Active% | PF | Net | Stress W/L | Pos weeks% | Delta pp | Recent3 | New kept | New net | Red flipped | Red worsened | New red net | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `baseline_supportive_guard` | 3645 | 50.40 | 2.0895 | 85.71 | 2.1395 | 20701.41 | 1.9720 | 57.69 | 0.00 | 279.22 | 0 | 0.00 | 0 | 0 | 0.00 | `BASELINE` |
| `bear_m5_ema_h1_only_rr2_morefreq_only` | 3996 | 48.70 | 2.1352 | 88.11 | 2.0408 | 20673.19 | 2.0136 | 55.50 | -2.19 | 442.65 | 353 | 3.20 | 7 | 25 | 57.00 | `REJECT_COMBINED_WR` |
| `bear_m5_ema_h1h4_rr2_strict_body_only` | 3994 | 48.57 | 2.1409 | 87.73 | 2.0360 | 20496.91 | 2.0183 | 57.42 | -0.27 | 300.15 | 350 | -194.02 | 7 | 24 | -84.79 | `REJECT_COMBINED_WR` |
| `bear_m5_ema_h1h4_rr2_fast_slope_only` | 3978 | 48.82 | 2.1296 | 87.82 | 2.0454 | 20649.85 | 2.0083 | 56.46 | -1.23 | 318.31 | 335 | -20.14 | 7 | 22 | 50.86 | `REJECT_COMBINED_WR` |
| `bear_ema_pullback_h1h4_rr2_only` | 4107 | 48.21 | 2.1467 | 88.02 | 2.0116 | 20506.15 | 2.0233 | 55.98 | -1.71 | 338.88 | 470 | -234.90 | 5 | 28 | -163.12 | `REJECT_COMBINED_WR` |
| `bear_break_run_h1h4_rr2_only` | 4064 | 48.45 | 2.1638 | 87.82 | 2.0474 | 20837.00 | 2.0390 | 58.17 | 0.48 | 369.06 | 420 | 138.06 | 5 | 25 | -23.36 | `REJECT_COMBINED_WR` |
| `bear_all_improvement_cells` | 4895 | 45.62 | 2.2212 | 88.30 | 1.8731 | 20623.99 | 2.0896 | 55.98 | -1.71 | 567.93 | 1261 | -83.17 | 10 | 23 | 0.34 | `REJECT_COMBINED_WR` |

## Interpretation

No variant beat the reference on both more trades and better WR while preserving payoff. Best diagnostic was `bear_ema_pullback_h1h4_rr2`: 487 trades, WR 31.42%, W/L 2.0018, net -186.96 USD. Do not tune hours from this output.

## Artifacts

- md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_BEAR_ENGINE_IMPROVEMENT_EXACT_202207_202606.md`
- json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_BEAR_ENGINE_IMPROVEMENT_EXACT_202207_202606.json`
- results_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_BEAR_ENGINE_IMPROVEMENT_EXACT_202207_202606_RESULTS.csv`
- standalone_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_BEAR_ENGINE_IMPROVEMENT_EXACT_202207_202606_STANDALONE.csv`
- mt5_components_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_BEAR_ENGINE_IMPROVEMENT_EXACT_202207_202606_MT5_COMPONENTS.md`
- mt5_components_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_BEAR_ENGINE_IMPROVEMENT_EXACT_202207_202606_MT5_COMPONENTS.json`
- bear_m5_ema_h1_only_rr2_morefreq_only_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_BEAR_ENGINE_IMPROVEMENT_EXACT_202207_202606_bear_m5_ema_h1_only_rr2_morefreq_only_KEPT.csv`
- bear_m5_ema_h1_only_rr2_morefreq_only_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_BEAR_ENGINE_IMPROVEMENT_EXACT_202207_202606_bear_m5_ema_h1_only_rr2_morefreq_only_DROPPED.csv`
- bear_m5_ema_h1h4_rr2_strict_body_only_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_BEAR_ENGINE_IMPROVEMENT_EXACT_202207_202606_bear_m5_ema_h1h4_rr2_strict_body_only_KEPT.csv`
- bear_m5_ema_h1h4_rr2_strict_body_only_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_BEAR_ENGINE_IMPROVEMENT_EXACT_202207_202606_bear_m5_ema_h1h4_rr2_strict_body_only_DROPPED.csv`
- bear_m5_ema_h1h4_rr2_fast_slope_only_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_BEAR_ENGINE_IMPROVEMENT_EXACT_202207_202606_bear_m5_ema_h1h4_rr2_fast_slope_only_KEPT.csv`
- bear_m5_ema_h1h4_rr2_fast_slope_only_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_BEAR_ENGINE_IMPROVEMENT_EXACT_202207_202606_bear_m5_ema_h1h4_rr2_fast_slope_only_DROPPED.csv`
- bear_ema_pullback_h1h4_rr2_only_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_BEAR_ENGINE_IMPROVEMENT_EXACT_202207_202606_bear_ema_pullback_h1h4_rr2_only_KEPT.csv`
- bear_ema_pullback_h1h4_rr2_only_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_BEAR_ENGINE_IMPROVEMENT_EXACT_202207_202606_bear_ema_pullback_h1h4_rr2_only_DROPPED.csv`
- bear_break_run_h1h4_rr2_only_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_BEAR_ENGINE_IMPROVEMENT_EXACT_202207_202606_bear_break_run_h1h4_rr2_only_KEPT.csv`
- bear_break_run_h1h4_rr2_only_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_BEAR_ENGINE_IMPROVEMENT_EXACT_202207_202606_bear_break_run_h1h4_rr2_only_DROPPED.csv`
- bear_all_improvement_cells_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_BEAR_ENGINE_IMPROVEMENT_EXACT_202207_202606_bear_all_improvement_cells_KEPT.csv`
- bear_all_improvement_cells_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_BEAR_ENGINE_IMPROVEMENT_EXACT_202207_202606_bear_all_improvement_cells_DROPPED.csv`
