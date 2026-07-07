# A1 XAU H4/D1 Review Repair Exact MT5 Probe

Generated UTC: `2026-07-07T10:47:01Z`

Scope: two preregistered H4/D1-only exact-MT5 repair probes, recomposed into the current F67-H16 no-f33 frontier. Frequency rows are unchanged. No live/demo runtime, chart, preset, order, position, or broker state was changed.

Status: `NO_H4_D1_REVIEW_REPAIR_SURVIVOR`
Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_H4_D1_REVIEW_REPAIR_PREREG_2026_07_07.md`
Preregistration SHA256: `10e8f6ad64d9f0255263ba897d5ef2efd865c9b6d87251bcc5716cd12b59a3f2`

## Results

| Probe | Signals | WR% | W/L | Active% | PF | Net | Stress -0.30 W/L | Positive weeks% | Worst week | Recent3 net | May net | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `baseline_f67_h16_no_f33` | 3751 | 50.23 | 2.0002 | 86.39 | 2.0336 | 22294.46 | 1.9029 | 54.81 | -878.18 | -1226.32 | -1055.98 | `BASELINE` |
| `supportive_guard` | 3653 | 50.40 | 2.0892 | 85.71 | 2.1392 | 20921.07 | 1.9730 | 57.21 | -878.18 | 279.22 | -142.12 | `FAIL_WEEKLY_SHAPE` |
| `weekly_loss_governor` | 3763 | 50.23 | 1.9913 | 86.48 | 2.0245 | 22367.87 | 1.8953 | 54.33 | -878.18 | -1226.32 | -1055.98 | `FAIL_CORE_WR_WL` |

## Pass-Fail Checks

### `supportive_guard`

- `wr_ge_50`: `True`
- `wl_ge_2`: `True`
- `active_ge_84`: `True`
- `stress_wl_ge_1p90`: `True`
- `recent3_improves_750`: `True`
- `may_improves_500`: `True`
- `positive_weeks_plus_3pp`: `False`
- `net_ge_17500`: `True`
- `worst_week_improves_20pct`: `False`

### `weekly_loss_governor`

- `wr_ge_50`: `True`
- `wl_ge_2`: `False`
- `active_ge_84`: `True`
- `stress_wl_ge_1p90`: `False`
- `recent3_improves_750`: `False`
- `may_improves_500`: `False`
- `positive_weeks_plus_3pp`: `False`
- `net_ge_17500`: `True`
- `worst_week_improves_20pct`: `False`

## H4/D1 MT5 Guard Counts

| Variant | Orders | h4_d1_supportive_state_guard | h4_d1_weekly_loss_governor | Other guard blocks |
| --- | ---: | ---: | ---: | ---: |
| `supportive_guard_box2` | 633 | 119 | 0 | 270 |
| `supportive_guard_broad` | 359 | 51 | 0 | 142 |
| `weekly_loss_governor_box2` | 633 | 0 | 3 | 270 |
| `weekly_loss_governor_broad` | 359 | 0 | 0 | 142 |

## Source Contributions


### `supportive_guard`

| Source | Signals | Net USD |
| --- | ---: | ---: |
| `freq_step3_frontier` | 3418 | 6145.46 |
| `h4_d1_long_best_box2_atr80` | 233 | 14256.74 |
| `h4_d1_long_broad_box3_atr60` | 2 | 518.87 |

### `weekly_loss_governor`

| Source | Signals | Net USD |
| --- | ---: | ---: |
| `freq_step3_frontier` | 3417 | 6161.63 |
| `h4_d1_long_best_box2_atr80` | 344 | 15687.37 |
| `h4_d1_long_broad_box3_atr60` | 2 | 518.87 |

## Interpretation

No preregistered H4/D1 repair probe passed. Best diagnostic by recent repair was `supportive_guard` with recent3 improvement 1505.54 USD and positive-week delta 2.40pp. Per preregistration, if both fail this repair path should be frozen and the next work should be a genuinely new red-week source class, not more H4/D1 masking.

## Artifacts

- md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_D1_REVIEW_REPAIR_EXACT_202207_202606.md`
- json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_D1_REVIEW_REPAIR_EXACT_202207_202606.json`
- results_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_D1_REVIEW_REPAIR_EXACT_202207_202606_RESULTS.csv`
- mt5_components_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_D1_REVIEW_REPAIR_EXACT_202207_202606_MT5_COMPONENTS.md`
- mt5_components_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_D1_REVIEW_REPAIR_EXACT_202207_202606_MT5_COMPONENTS.json`
- supportive_guard_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_D1_REVIEW_REPAIR_EXACT_202207_202606_supportive_guard_KEPT.csv`
- supportive_guard_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_D1_REVIEW_REPAIR_EXACT_202207_202606_supportive_guard_DROPPED.csv`
- weekly_loss_governor_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_D1_REVIEW_REPAIR_EXACT_202207_202606_weekly_loss_governor_KEPT.csv`
- weekly_loss_governor_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_D1_REVIEW_REPAIR_EXACT_202207_202606_weekly_loss_governor_DROPPED.csv`
