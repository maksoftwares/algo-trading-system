# A1 XAU H4 Box2 Health Gate + Third-Entry Quality Exact MT5

Generated UTC: `2026-07-08T08:05:13Z`

Scope: one exact-MT5 H4/D1 box2 rerun with supportive guard, previous-month health gate, and a third-entry H4 quality gate; broad H4/D1 is quarantined. No live/demo runtime, chart, preset, order, position, or broker state was changed.

Status: `H4_BOX2_THIRD_ENTRY_QUALITY_CORE_ONLY`
Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_H4_BOX2_HEALTH_THIRD_ENTRY_QUALITY_EXACT_PREREG_2026_07_08.md`
Preregistration SHA256: `1d2ccbfe234c6aae11be2efbedbd3d233f5eedac138cfb3462f4d306d31cdfd1`

## Results

| Row | Decision | Signals | Blocked | WR% | W/L | Stress W/L | Active% | Net | Max DD | +Months | -Months | Pos weeks% | Worst month | Worst month net | Worst week |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| `prevhealth_box2_broad_quarantined` | `BASELINE` | 3934 | 0 | 49.08 | 2.1793 | 2.0507 | 87.44 | 20858.29 | 958.86 | 31 | 17 | 58.10 | `2023-02` | -405.08 | -878.18 |
| `prevhealth_box2_third_entry_quality_broad_quarantined` | `H4_BOX2_THIRD_ENTRY_QUALITY_CORE_ONLY` | 3927 | 31 | 48.99 | 2.1415 | 2.0142 | 87.44 | 20032.25 | 958.86 | 31 | 17 | 58.10 | `2023-02` | -405.08 | -878.18 |

## Source Contributions

| Source | Signals | Net USD |
| --- | ---: | ---: |
| `freq_step3_frontier` | 3417 | 6127.72 |
| `h4_d1_long_best_box2_atr80` | 201 | 13523.53 |
| `short_hedge_v2_breakdown_retest` | 309 | 381.00 |

## MT5 Guard Counts

- Orders: `633`
- Third-entry quality blocks: `7`
- Previous-month health blocks: `17`
- Supportive-state blocks: `112`

## Interpretation

The third-entry quality gate preserved the core but did not repair the weekly tail. Same-day third-entry H4 quality is not enough.

## Artifacts

- report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_THIRD_ENTRY_QUALITY_EXACT_202207_202606.md`
- report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_THIRD_ENTRY_QUALITY_EXACT_202207_202606.json`
- results_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_THIRD_ENTRY_QUALITY_EXACT_202207_202606_RESULTS.csv`
- kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_THIRD_ENTRY_QUALITY_EXACT_202207_202606_KEPT.csv`
- dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_THIRD_ENTRY_QUALITY_EXACT_202207_202606_DROPPED.csv`
- mt5_component_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_THIRD_ENTRY_QUALITY_EXACT_202207_202606_MT5_COMPONENT.md`
- mt5_component_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_THIRD_ENTRY_QUALITY_EXACT_202207_202606_MT5_COMPONENT.json`
