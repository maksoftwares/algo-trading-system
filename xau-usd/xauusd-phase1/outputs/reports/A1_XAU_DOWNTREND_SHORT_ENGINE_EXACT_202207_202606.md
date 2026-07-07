# A1 XAU Downtrend Short Engine Exact MT5 Probe

Generated UTC: `2026-07-07T12:37:57Z`

Scope: four preregistered bearish-D1 short-engine variants, recomposed onto the corrected supportive-guard uptrend baseline. No live/demo runtime, chart, preset, order, position, or broker state was changed.

Status: `DOWNTREND_SHORT_STANDALONE_CLUE_NO_COMBINED_SURVIVOR`
Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_DOWNTREND_SHORT_ENGINE_PREREG_2026_07_07.md`
Preregistration SHA256: `6978091ec77b247f8a7d030e42ad73f5a9cc0a10ffa9f22b949bf71a2aeba681`

## Combined Results

| Combo | Signals | WR% | W/L | Active% | PF | Net | Stress W/L | Pos weeks% | Delta pp | Worst week | Recent3 | May | New kept | New net | Red touched | Red flipped | Red worsened | New red net | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `baseline_supportive_guard` | 3645 | 50.40 | 2.0895 | 85.71 | 2.1395 | 20701.41 | 1.9720 | 57.69 | 0.00 | -878.18 | 279.22 | -142.12 | 0 | 0.00 | 0 | 0 | 0 | 0.00 | `BASELINE` |
| `down_h4_d1_short_box2_atr80_only` | 3747 | 49.77 | 1.9477 | 86.39 | 1.9446 | 19710.14 | 1.8472 | 51.92 | -5.77 | -878.18 | 279.22 | -142.12 | 103 | -993.77 | 16 | 6 | 10 | 44.74 | `REJECT_BREAKS_CORE_SHAPE` |
| `down_h1_d1_short_box2_atr80_only` | 3820 | 49.45 | 1.9187 | 86.10 | 1.8907 | 19783.87 | 1.8235 | 54.33 | -3.36 | -878.18 | 279.22 | -142.12 | 179 | -936.09 | 11 | 5 | 6 | 492.01 | `REJECT_BREAKS_CORE_SHAPE` |
| `down_m5_ema_h1h4_short_rr2_only` | 3993 | 48.74 | 2.1343 | 87.82 | 2.0429 | 20681.85 | 2.0127 | 57.42 | -0.27 | -878.18 | 414.85 | -201.10 | 350 | 11.86 | 38 | 8 | 24 | 25.35 | `REJECT_BREAKS_CORE_SHAPE` |
| `down_prior_day_cont_short_rr2_only` | 3987 | 48.68 | 2.1583 | 87.15 | 2.0616 | 20557.96 | 2.0327 | 56.94 | -0.75 | -878.18 | 452.34 | -136.87 | 343 | -152.23 | 34 | 4 | 26 | -137.92 | `REJECT_BREAKS_CORE_SHAPE` |
| `down_all_short_engines` | 4538 | 46.56 | 1.9582 | 88.11 | 1.7161 | 19116.02 | 1.8600 | 51.67 | -6.02 | -878.18 | 618.02 | -195.85 | 901 | -1583.80 | 41 | 10 | 28 | 371.40 | `REJECT_BREAKS_CORE_SHAPE` |

## Standalone Downtrend Rows

| Variant | Trades | WR% | W/L | Active% | PF | Net | Stress W/L | Pos weeks% | Worst week | Recent3 | Diagnostic |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `down_h4_d1_short_box2_atr80` | 103 | 27.18 | 1.6934 | 6.23 | 0.6322 | -993.77 | 1.6711 | 28.21 | -239.18 | 0.00 | `STANDALONE_REJECT` |
| `down_h1_d1_short_box2_atr80` | 181 | 29.28 | 1.8366 | 4.99 | 0.7605 | -986.04 | 1.8104 | 33.33 | -489.46 | 0.00 | `STANDALONE_REJECT` |
| `down_m5_ema_h1h4_short_rr2` | 438 | 33.11 | 2.1595 | 18.50 | 1.0687 | 137.34 | 2.0264 | 42.86 | -49.81 | 258.45 | `STANDALONE_SHORT_CLUE` |
| `down_prior_day_cont_short_rr2` | 354 | 30.23 | 1.9871 | 13.52 | 0.8608 | -175.48 | 1.8212 | 25.35 | -40.96 | 159.62 | `STANDALONE_REJECT` |

## Pass-Fail Checks


### `down_h4_d1_short_box2_atr80_only`

- `wr_ge_50`: `False`
- `wl_ge_2`: `False`
- `active_ge_85`: `True`
- `stress_wl_ge_1p90`: `False`
- `positive_weeks_plus_3pp`: `False`
- `red_weeks_flipped_ge_8`: `False`
- `red_weeks_worsened_le_4`: `False`
- `new_red_week_net_ge_300`: `False`
- `worst_week_improved`: `False`

### `down_h1_d1_short_box2_atr80_only`

- `wr_ge_50`: `False`
- `wl_ge_2`: `False`
- `active_ge_85`: `True`
- `stress_wl_ge_1p90`: `False`
- `positive_weeks_plus_3pp`: `False`
- `red_weeks_flipped_ge_8`: `False`
- `red_weeks_worsened_le_4`: `False`
- `new_red_week_net_ge_300`: `True`
- `worst_week_improved`: `False`

### `down_m5_ema_h1h4_short_rr2_only`

- `wr_ge_50`: `False`
- `wl_ge_2`: `True`
- `active_ge_85`: `True`
- `stress_wl_ge_1p90`: `True`
- `positive_weeks_plus_3pp`: `False`
- `red_weeks_flipped_ge_8`: `True`
- `red_weeks_worsened_le_4`: `False`
- `new_red_week_net_ge_300`: `False`
- `worst_week_improved`: `False`

### `down_prior_day_cont_short_rr2_only`

- `wr_ge_50`: `False`
- `wl_ge_2`: `True`
- `active_ge_85`: `True`
- `stress_wl_ge_1p90`: `True`
- `positive_weeks_plus_3pp`: `False`
- `red_weeks_flipped_ge_8`: `False`
- `red_weeks_worsened_le_4`: `False`
- `new_red_week_net_ge_300`: `False`
- `worst_week_improved`: `False`

### `down_all_short_engines`

- `wr_ge_50`: `False`
- `wl_ge_2`: `False`
- `active_ge_85`: `True`
- `stress_wl_ge_1p90`: `False`
- `positive_weeks_plus_3pp`: `False`
- `red_weeks_flipped_ge_8`: `True`
- `red_weeks_worsened_le_4`: `False`
- `new_red_week_net_ge_300`: `True`
- `worst_week_improved`: `False`

## MT5 Guard Counts

| Variant | Trades | Orders | d1_support_state_gate | Other guard blocks |
| --- | ---: | ---: | ---: | ---: |
| `down_h4_d1_short_box2_atr80` | 103 | 504 | 116 | 284 |
| `down_h1_d1_short_box2_atr80` | 181 | 587 | 102 | 303 |
| `down_m5_ema_h1h4_short_rr2` | 438 | 37103 | 1068 | 35597 |
| `down_prior_day_cont_short_rr2` | 354 | 21930 | 5427 | 16149 |

## Interpretation

No combined uptrend+downtrend row passed, but `down_m5_ema_h1h4_short_rr2` is a standalone bearish clue (438 trades, WR 33.11%, W/L 2.1595, net 137.34 USD). Best combined diagnostic was `down_m5_ema_h1h4_short_rr2_only` with -0.27pp positive-week delta. Review only if the owner accepts a separate low-frequency downtrend branch; do not tune hours from this output.

## Artifacts

- md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_DOWNTREND_SHORT_ENGINE_EXACT_202207_202606.md`
- json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_DOWNTREND_SHORT_ENGINE_EXACT_202207_202606.json`
- results_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_DOWNTREND_SHORT_ENGINE_EXACT_202207_202606_RESULTS.csv`
- standalone_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_DOWNTREND_SHORT_ENGINE_EXACT_202207_202606_STANDALONE.csv`
- mt5_components_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_DOWNTREND_SHORT_ENGINE_EXACT_202207_202606_MT5_COMPONENTS.md`
- mt5_components_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_DOWNTREND_SHORT_ENGINE_EXACT_202207_202606_MT5_COMPONENTS.json`
- down_h4_d1_short_box2_atr80_only_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_DOWNTREND_SHORT_ENGINE_EXACT_202207_202606_down_h4_d1_short_box2_atr80_only_KEPT.csv`
- down_h4_d1_short_box2_atr80_only_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_DOWNTREND_SHORT_ENGINE_EXACT_202207_202606_down_h4_d1_short_box2_atr80_only_DROPPED.csv`
- down_h1_d1_short_box2_atr80_only_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_DOWNTREND_SHORT_ENGINE_EXACT_202207_202606_down_h1_d1_short_box2_atr80_only_KEPT.csv`
- down_h1_d1_short_box2_atr80_only_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_DOWNTREND_SHORT_ENGINE_EXACT_202207_202606_down_h1_d1_short_box2_atr80_only_DROPPED.csv`
- down_m5_ema_h1h4_short_rr2_only_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_DOWNTREND_SHORT_ENGINE_EXACT_202207_202606_down_m5_ema_h1h4_short_rr2_only_KEPT.csv`
- down_m5_ema_h1h4_short_rr2_only_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_DOWNTREND_SHORT_ENGINE_EXACT_202207_202606_down_m5_ema_h1h4_short_rr2_only_DROPPED.csv`
- down_prior_day_cont_short_rr2_only_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_DOWNTREND_SHORT_ENGINE_EXACT_202207_202606_down_prior_day_cont_short_rr2_only_KEPT.csv`
- down_prior_day_cont_short_rr2_only_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_DOWNTREND_SHORT_ENGINE_EXACT_202207_202606_down_prior_day_cont_short_rr2_only_DROPPED.csv`
- down_all_short_engines_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_DOWNTREND_SHORT_ENGINE_EXACT_202207_202606_down_all_short_engines_KEPT.csv`
- down_all_short_engines_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_DOWNTREND_SHORT_ENGINE_EXACT_202207_202606_down_all_short_engines_DROPPED.csv`
