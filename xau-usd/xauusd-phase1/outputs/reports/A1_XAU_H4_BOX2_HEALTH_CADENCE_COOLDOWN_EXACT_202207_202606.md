# A1 XAU H4 Box2 Health Gate + Cadence Cooldown Exact MT5

Generated UTC: `2026-07-08T09:58:21Z`

Scope: one exact-MT5 H4/D1 box2 rerun with supportive guard, previous-month health gate, and 480-minute cooldown; broad H4/D1 is quarantined. No live/demo runtime, chart, preset, order, position, or broker state was changed.

Status: `NO_H4_BOX2_CADENCE_COOLDOWN_SURVIVOR`
Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_H4_BOX2_HEALTH_CADENCE_COOLDOWN_EXACT_PREREG_2026_07_08.md`
Preregistration SHA256: `b23868b5058b62c4ae7d7f6afa0f2aa640a743f9b5a920976a2643d4fb5a4d9f`

## Results

| Row | Decision | Signals | Blocked | WR% | W/L | Stress W/L | Active% | Net | Max DD | +Months | -Months | Pos weeks% | Worst month | Worst month net | Worst week |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| `prevhealth_box2_broad_quarantined` | `BASELINE` | 3934 | 0 | 49.08 | 2.1793 | 2.0507 | 87.44 | 20858.29 | 958.86 | 31 | 17 | 58.10 | `2023-02` | -405.08 | -878.18 |
| `prevhealth_box2_cadence_cooldown_broad_quarantined` | `NO_H4_BOX2_CADENCE_COOLDOWN_SURVIVOR` | 3900 | 29 | 48.79 | 1.9941 | 1.8697 | 87.44 | 16753.61 | 853.84 | 31 | 17 | 57.14 | `2023-02` | -405.08 | -773.16 |

## Source Contributions

| Source | Signals | Net USD |
| --- | ---: | ---: |
| `freq_step3_frontier` | 3417 | 6127.72 |
| `h4_d1_long_best_box2_atr80` | 174 | 10244.89 |
| `short_hedge_v2_breakdown_retest` | 309 | 381.00 |

## MT5 Guard Counts

- Orders: `633`
- Cooldown blocks: `37`
- Previous-month health blocks: `17`
- Supportive-state blocks: `112`

## Interpretation

The cadence cooldown broke the core candidate. Do not promote.

## Artifacts

- report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_CADENCE_COOLDOWN_EXACT_202207_202606.md`
- report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_CADENCE_COOLDOWN_EXACT_202207_202606.json`
- results_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_CADENCE_COOLDOWN_EXACT_202207_202606_RESULTS.csv`
- kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_CADENCE_COOLDOWN_EXACT_202207_202606_KEPT.csv`
- dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_CADENCE_COOLDOWN_EXACT_202207_202606_DROPPED.csv`
- mt5_component_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_CADENCE_COOLDOWN_EXACT_202207_202606_MT5_COMPONENT.md`
- mt5_component_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_CADENCE_COOLDOWN_EXACT_202207_202606_MT5_COMPONENT.json`
