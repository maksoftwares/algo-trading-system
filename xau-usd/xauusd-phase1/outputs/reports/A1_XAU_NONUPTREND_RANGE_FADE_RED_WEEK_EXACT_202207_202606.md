# A1 XAU Non-Uptrend Range-Fade Red-Week Exact MT5 Probe

Generated UTC: `2026-07-07T12:19:49Z`

Scope: three preregistered exact-MT5 non-uptrend range-fade variants, recomposed onto the corrected supportive-guard book. No live/demo runtime, chart, preset, order, position, or broker state was changed.

Status: `NO_NONUPTREND_RANGE_FADE_RED_WEEK_SURVIVOR`
Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_NONUPTREND_RANGE_FADE_RED_WEEK_PREREG_2026_07_07.md`
Preregistration SHA256: `add7051334c9de7560560b81688ea5a595816d75f9062355fd468a738df80d9d`

## Results

| Combo | Signals | WR% | W/L | Active% | PF | Net | Stress W/L | Pos weeks% | Delta pp | Worst week | Recent3 | May | New kept | New net | Red touched | Red flipped | Red worsened | New red net | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `baseline_supportive_guard` | 3645 | 50.40 | 2.0895 | 85.71 | 2.1395 | 20701.41 | 1.9720 | 57.69 | 0.00 | -878.18 | 279.22 | -142.12 | 0 | 0.00 | 0 | 0 | 0 | 0.00 | `BASELINE` |
| `nonup_daily_extreme_rr2_only` | 3866 | 49.43 | 2.0700 | 87.34 | 2.0380 | 20405.12 | 1.9547 | 57.21 | -0.48 | -878.18 | 79.86 | -295.37 | 222 | -300.32 | 35 | 6 | 18 | 78.90 | `REJECT_BREAKS_CORE_SHAPE` |
| `nonup_prior_day_reversal_rr2_only` | 4125 | 48.51 | 2.1772 | 88.40 | 2.0648 | 20727.62 | 2.0474 | 58.65 | 0.96 | -880.97 | 237.86 | -75.42 | 481 | 21.76 | 58 | 8 | 32 | 30.61 | `REJECT_BREAKS_CORE_SHAPE` |
| `nonup_orrev_london_rr2_only` | 3702 | 50.22 | 2.0955 | 85.91 | 2.1298 | 20721.60 | 1.9769 | 57.21 | -0.48 | -878.18 | 257.94 | -149.85 | 58 | 17.68 | 22 | 1 | 14 | -7.04 | `REJECT_WEEKLY_NOT_IMPROVED` |
| `nonup_all_range_fade_rr2` | 4395 | 47.62 | 2.1516 | 89.55 | 1.9682 | 20439.99 | 2.0244 | 58.65 | 0.96 | -880.97 | 17.22 | -236.40 | 753 | -272.41 | 60 | 12 | 31 | 101.39 | `REJECT_BREAKS_CORE_SHAPE` |

## Pass-Fail Checks


### `nonup_daily_extreme_rr2_only`

- `wr_ge_50`: `False`
- `wl_ge_2`: `True`
- `active_ge_85`: `True`
- `stress_wl_ge_1p90`: `True`
- `positive_weeks_plus_3pp`: `False`
- `red_weeks_flipped_ge_8`: `False`
- `red_weeks_worsened_le_4`: `False`
- `new_red_week_net_ge_300`: `False`
- `worst_week_improved`: `False`

### `nonup_prior_day_reversal_rr2_only`

- `wr_ge_50`: `False`
- `wl_ge_2`: `True`
- `active_ge_85`: `True`
- `stress_wl_ge_1p90`: `True`
- `positive_weeks_plus_3pp`: `False`
- `red_weeks_flipped_ge_8`: `True`
- `red_weeks_worsened_le_4`: `False`
- `new_red_week_net_ge_300`: `False`
- `worst_week_improved`: `False`

### `nonup_orrev_london_rr2_only`

- `wr_ge_50`: `True`
- `wl_ge_2`: `True`
- `active_ge_85`: `True`
- `stress_wl_ge_1p90`: `True`
- `positive_weeks_plus_3pp`: `False`
- `red_weeks_flipped_ge_8`: `False`
- `red_weeks_worsened_le_4`: `False`
- `new_red_week_net_ge_300`: `False`
- `worst_week_improved`: `False`

### `nonup_all_range_fade_rr2`

- `wr_ge_50`: `False`
- `wl_ge_2`: `True`
- `active_ge_85`: `True`
- `stress_wl_ge_1p90`: `True`
- `positive_weeks_plus_3pp`: `False`
- `red_weeks_flipped_ge_8`: `True`
- `red_weeks_worsened_le_4`: `False`
- `new_red_week_net_ge_300`: `False`
- `worst_week_improved`: `False`

## MT5 Guard Counts

| Variant | Trades | Orders | d1_support_state_gate | Other guard blocks |
| --- | ---: | ---: | ---: | ---: |
| `nonup_daily_extreme_rr2` | 224 | 682 | 454 | 4 |
| `nonup_prior_day_reversal_rr2` | 506 | 2051 | 1135 | 410 |
| `nonup_orrev_london_rr2` | 629 | 2667 | 1443 | 595 |

## Interpretation

No non-uptrend range-fade combo passed. Best diagnostic by weekly repair was `nonup_all_range_fade_rr2` with 0.96pp positive-week delta, 12 red weeks flipped, and 101.39 USD new-source net in baseline red weeks. Per preregistration, do not tune hours or thresholds from this output; freeze or move to a different source class.

## Artifacts

- md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_NONUPTREND_RANGE_FADE_RED_WEEK_EXACT_202207_202606.md`
- json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_NONUPTREND_RANGE_FADE_RED_WEEK_EXACT_202207_202606.json`
- results_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_NONUPTREND_RANGE_FADE_RED_WEEK_EXACT_202207_202606_RESULTS.csv`
- mt5_components_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_NONUPTREND_RANGE_FADE_RED_WEEK_EXACT_202207_202606_MT5_COMPONENTS.md`
- mt5_components_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_NONUPTREND_RANGE_FADE_RED_WEEK_EXACT_202207_202606_MT5_COMPONENTS.json`
- nonup_daily_extreme_rr2_only_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_NONUPTREND_RANGE_FADE_RED_WEEK_EXACT_202207_202606_nonup_daily_extreme_rr2_only_KEPT.csv`
- nonup_daily_extreme_rr2_only_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_NONUPTREND_RANGE_FADE_RED_WEEK_EXACT_202207_202606_nonup_daily_extreme_rr2_only_DROPPED.csv`
- nonup_prior_day_reversal_rr2_only_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_NONUPTREND_RANGE_FADE_RED_WEEK_EXACT_202207_202606_nonup_prior_day_reversal_rr2_only_KEPT.csv`
- nonup_prior_day_reversal_rr2_only_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_NONUPTREND_RANGE_FADE_RED_WEEK_EXACT_202207_202606_nonup_prior_day_reversal_rr2_only_DROPPED.csv`
- nonup_orrev_london_rr2_only_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_NONUPTREND_RANGE_FADE_RED_WEEK_EXACT_202207_202606_nonup_orrev_london_rr2_only_KEPT.csv`
- nonup_orrev_london_rr2_only_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_NONUPTREND_RANGE_FADE_RED_WEEK_EXACT_202207_202606_nonup_orrev_london_rr2_only_DROPPED.csv`
- nonup_all_range_fade_rr2_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_NONUPTREND_RANGE_FADE_RED_WEEK_EXACT_202207_202606_nonup_all_range_fade_rr2_KEPT.csv`
- nonup_all_range_fade_rr2_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_NONUPTREND_RANGE_FADE_RED_WEEK_EXACT_202207_202606_nonup_all_range_fade_rr2_DROPPED.csv`
