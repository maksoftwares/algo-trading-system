# A1 XAU H4 Box2 Health Gate + Negative Stack Guard Exact MT5

Generated UTC: `2026-07-08T07:51:51Z`

Scope: one exact-MT5 H4/D1 box2 rerun with supportive guard, previous-month health gate, and negative-stack guard; broad H4/D1 is quarantined. No live/demo runtime, chart, preset, order, position, or broker state was changed.

Status: `H4_BOX2_NEGATIVE_STACK_CORE_ONLY`
Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_H4_BOX2_HEALTH_NEGATIVE_STACK_EXACT_PREREG_2026_07_08.md`
Preregistration SHA256: `9a6560cee0fd25a325d54f94684d94ca516cfe6c15d37e1513a43bac312b19d6`

## Results

| Row | Decision | Signals | Blocked | WR% | W/L | Stress W/L | Active% | Net | Max DD | +Months | -Months | Pos weeks% | Worst month | Worst month net | Worst week |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| `prevhealth_box2_broad_quarantined` | `BASELINE` | 3934 | 0 | 49.08 | 2.1793 | 2.0507 | 87.44 | 20858.29 | 958.86 | 31 | 17 | 58.10 | `2023-02` | -405.08 | -878.18 |
| `prevhealth_box2_negative_stack_broad_quarantined` | `H4_BOX2_NEGATIVE_STACK_CORE_ONLY` | 3933 | 31 | 49.10 | 2.1862 | 2.0569 | 87.44 | 20927.09 | 958.86 | 31 | 17 | 58.10 | `2023-02` | -405.08 | -878.18 |

## Source Contributions

| Source | Signals | Net USD |
| --- | ---: | ---: |
| `freq_step3_frontier` | 3417 | 6127.72 |
| `h4_d1_long_best_box2_atr80` | 207 | 14418.37 |
| `short_hedge_v2_breakdown_retest` | 309 | 381.00 |

## MT5 Guard Counts

- Orders: `633`
- Negative-stack blocks: `1`
- Previous-month health blocks: `17`
- Supportive-state blocks: `112`

## Interpretation

The negative-stack guard preserved the core but did not repair the weekly tail. The weekly damage is not sufficiently caused by underwater stacking.

## Artifacts

- report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_NEGATIVE_STACK_EXACT_202207_202606.md`
- report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_NEGATIVE_STACK_EXACT_202207_202606.json`
- results_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_NEGATIVE_STACK_EXACT_202207_202606_RESULTS.csv`
- kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_NEGATIVE_STACK_EXACT_202207_202606_KEPT.csv`
- dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_NEGATIVE_STACK_EXACT_202207_202606_DROPPED.csv`
- mt5_component_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_NEGATIVE_STACK_EXACT_202207_202606_MT5_COMPONENT.md`
- mt5_component_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_NEGATIVE_STACK_EXACT_202207_202606_MT5_COMPONENT.json`
