# A1 XAU H4 Previous-Month Health Gate Exact MT5

Generated UTC: `2026-07-08T07:25:39Z`

Scope: exact-MT5 H4 component rerun with previous-month health gate, recomposed with existing exact-MT5 frequency and V2 short ledgers. No live/demo runtime, chart, preset, order, position, or broker state was changed.

Status: `EXACT_SOURCE_HEALTH_WATCHLIST`
Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_H4_PREVIOUS_MONTH_HEALTH_GATE_EXACT_PREREG_2026_07_08.md`
Preregistration SHA256: `4aa681a82395659d47bd091cb40646b0e63ff8c740a3c9dcfa6102a8a1c9d935`

## Results

| Row | Decision | Signals | Blocked | WR% | W/L | Stress W/L | Active% | Net | Max DD | +Months | -Months | Pos weeks% | Worst month | Worst month net | Worst week |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| `long_plus_short_v2_no_source_health_gate` | `BASELINE` | 3953 | 0 | 49.00 | 2.1637 | 2.0390 | 87.54 | 21064.67 | 958.86 | 29 | 19 | 57.62 | `2023-02` | -405.08 | -878.18 |
| `h4_prev_month_health_gate_exact` | `EXACT_SOURCE_HEALTH_WATCHLIST` | 3944 | 166 | 49.06 | 2.1636 | 2.0385 | 87.54 | 21022.69 | 1032.27 | 31 | 17 | 58.10 | `2025-07` | -495.22 | -878.18 |

## MT5 Guard Counts

| Variant | Trades | Orders | previous-month health blocks | supportive-state blocks | other guard blocks |
| --- | ---: | ---: | ---: | ---: | ---: |
| `h4_prev_month_health_gate_box2` | 216 | 633 | 17 | 112 | 285 |
| `h4_prev_month_health_gate_broad` | 145 | 359 | 13 | 47 | 152 |

## Source Contributions

| Source | Signals | Net USD |
| --- | ---: | ---: |
| `freq_step3_frontier` | 3417 | 6127.72 |
| `h4_d1_long_best_box2_atr80` | 208 | 14349.57 |
| `h4_d1_long_broad_box3_atr60` | 10 | 164.40 |
| `short_hedge_v2_breakdown_retest` | 309 | 381.00 |

## Interpretation

The exact-MT5 component-local previous-month H4 health gate preserved the core and improved monthly consistency enough for watchlist. Next step is reviewer review or a true combined-H4 runtime if exact group-gating is required.

## Artifacts

- report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_PREVIOUS_MONTH_HEALTH_GATE_EXACT_202207_202606.md`
- report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_PREVIOUS_MONTH_HEALTH_GATE_EXACT_202207_202606.json`
- results_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_PREVIOUS_MONTH_HEALTH_GATE_EXACT_202207_202606_RESULTS.csv`
- kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_PREVIOUS_MONTH_HEALTH_GATE_EXACT_202207_202606_KEPT.csv`
- dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_PREVIOUS_MONTH_HEALTH_GATE_EXACT_202207_202606_DROPPED.csv`
- mt5_components_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_PREVIOUS_MONTH_HEALTH_GATE_EXACT_202207_202606_MT5_COMPONENTS.md`
- mt5_components_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_PREVIOUS_MONTH_HEALTH_GATE_EXACT_202207_202606_MT5_COMPONENTS.json`
