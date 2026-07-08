# A1 XAU H4 Box2 Health Gate + Open Cap 2 Exact MT5

Generated UTC: `2026-07-08T07:47:43Z`

Scope: one exact-MT5 H4/D1 box2 rerun with supportive guard, previous-month health gate, and open-position cap; broad H4/D1 is quarantined. No live/demo runtime, chart, preset, order, position, or broker state was changed.

Status: `NO_H4_BOX2_OPEN_CAP_SURVIVOR`
Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_H4_BOX2_HEALTH_OPEN_CAP_EXACT_PREREG_2026_07_08.md`
Preregistration SHA256: `8cf902f5acbfd72b0ec9e0fbf7b26ad77c8986a24729f0cbafe8c917aec6c78a`

## Results

| Row | Decision | Signals | Blocked | WR% | W/L | Stress W/L | Active% | Net | Max DD | +Months | -Months | Pos weeks% | Worst month | Worst month net | Worst week |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| `prevhealth_box2_broad_quarantined` | `BASELINE` | 3934 | 0 | 49.08 | 2.1793 | 2.0507 | 87.44 | 20858.29 | 958.86 | 31 | 17 | 58.10 | `2023-02` | -405.08 | -878.18 |
| `prevhealth_box2_open_cap2_broad_quarantined` | `REJECT_CORE_BREAK` | 3794 | 25 | 48.23 | 1.7101 | 1.5847 | 87.06 | 10064.02 | 629.25 | 32 | 16 | 56.67 | `2023-02` | -166.87 | -283.11 |

## Source Contributions

| Source | Signals | Net USD |
| --- | ---: | ---: |
| `freq_step3_frontier` | 3417 | 6127.72 |
| `h4_d1_long_best_box2_atr80` | 68 | 3555.30 |
| `short_hedge_v2_breakdown_retest` | 309 | 381.00 |

## MT5 Guard Counts

- Orders: `633`
- Max-open-position blocks: `145`
- Previous-month health blocks: `20`
- Supportive-state blocks: `112`

## Interpretation

The open-position cap broke the core candidate. Do not promote.

## Artifacts

- report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_OPEN_CAP2_EXACT_202207_202606.md`
- report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_OPEN_CAP2_EXACT_202207_202606.json`
- results_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_OPEN_CAP2_EXACT_202207_202606_RESULTS.csv`
- kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_OPEN_CAP2_EXACT_202207_202606_KEPT.csv`
- dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_OPEN_CAP2_EXACT_202207_202606_DROPPED.csv`
- mt5_component_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_OPEN_CAP2_EXACT_202207_202606_MT5_COMPONENT.md`
- mt5_component_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_OPEN_CAP2_EXACT_202207_202606_MT5_COMPONENT.json`
