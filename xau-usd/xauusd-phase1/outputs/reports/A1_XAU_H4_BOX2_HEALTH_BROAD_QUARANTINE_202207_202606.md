# A1 XAU H4 Box2 Health Gate / Broad Quarantine

Generated UTC: `2026-07-08T07:35:54Z`

Scope: recomposition of existing exact-MT5 H4 component ledgers with unchanged frequency and V2 short ledgers. No live/demo runtime, chart, preset, order, position, or broker state was changed.

Status: `H4_COMPOSITION_REVIEW_CANDIDATE`
Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_H4_BOX2_HEALTH_BROAD_QUARANTINE_PREREG_2026_07_08.md`
Preregistration SHA256: `10d29c07e3f7178a9303139aff35f3f11309f31b3fab7076f77dbe757465441e`

## Results

| Row | Decision | Signals | Blocked | WR% | W/L | Stress W/L | Active% | Net | Max DD | +Months | -Months | Pos weeks% | Worst month | Worst month net | Worst week |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| `long_plus_short_v2_no_source_health_gate` | `BASELINE` | 3953 | 0 | 49.00 | 2.1637 | 2.0390 | 87.54 | 21064.67 | 958.86 | 29 | 19 | 57.62 | `2023-02` | -405.08 | -878.18 |
| `control_supportive_box2_supportive_broad` | `H4_COMPOSITION_CORE_ONLY` | 3953 | 187 | 49.00 | 2.1637 | 2.0390 | 87.54 | 21064.67 | 958.86 | 29 | 19 | 57.62 | `2023-02` | -405.08 | -878.18 |
| `prevhealth_box2_supportive_broad` | `REJECT_CORE_OR_SHAPE` | 3948 | 175 | 49.01 | 2.1554 | 2.0311 | 87.54 | 20911.77 | 1032.27 | 30 | 18 | 57.62 | `2025-07` | -495.22 | -878.18 |
| `prevhealth_box2_broad_quarantined` | `H4_COMPOSITION_REVIEW_CANDIDATE` | 3934 | 31 | 49.08 | 2.1793 | 2.0507 | 87.44 | 20858.29 | 958.86 | 31 | 17 | 58.10 | `2023-02` | -405.08 | -878.18 |
| `supportive_box2_broad_quarantined` | `H4_COMPOSITION_CORE_ONLY` | 3951 | 31 | 48.97 | 2.1380 | 2.0143 | 87.54 | 20545.80 | 958.86 | 29 | 19 | 57.62 | `2023-02` | -405.08 | -878.18 |
| `prevhealth_box2_prevhealth_broad` | `H4_COMPOSITION_WATCHLIST_DD_OR_MONTH_RISK` | 3944 | 166 | 49.06 | 2.1636 | 2.0385 | 87.54 | 21022.69 | 1032.27 | 31 | 17 | 58.10 | `2025-07` | -495.22 | -878.18 |

## Best Source Contributions

| Source | Signals | Net USD |
| --- | ---: | ---: |
| `freq_step3_frontier` | 3417 | 6127.72 |
| `h4_d1_long_best_box2_atr80` | 208 | 14349.57 |
| `short_hedge_v2_breakdown_retest` | 309 | 381.00 |

## MT5 Component Guard Counts

| Component | Trades | Orders | Health blocks | Support blocks | Other guard blocks |
| --- | ---: | ---: | ---: | ---: | ---: |
| `supportive_guard_box2` | 233 | 633 | 0 | 112 | 285 |
| `supportive_guard_broad` | 158 | 359 | 0 | 47 | 152 |
| `h4_prev_month_health_gate_box2` | 216 | 633 | 17 | 112 | 285 |
| `h4_prev_month_health_gate_broad` | 145 | 359 | 13 | 47 | 152 |

## Interpretation

A broad-quarantine/box2-health composition repaired monthly consistency without worsening drawdown or worst month. It is still research-only, but this is now a reviewer-grade candidate.

## Artifacts

- report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_BROAD_QUARANTINE_202207_202606.md`
- report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_BROAD_QUARANTINE_202207_202606.json`
- results_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_BROAD_QUARANTINE_202207_202606_RESULTS.csv`
- control_supportive_box2_supportive_broad_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_BROAD_QUARANTINE_202207_202606_control_supportive_box2_supportive_broad_KEPT.csv`
- prevhealth_box2_supportive_broad_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_BROAD_QUARANTINE_202207_202606_prevhealth_box2_supportive_broad_KEPT.csv`
- prevhealth_box2_broad_quarantined_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_BROAD_QUARANTINE_202207_202606_prevhealth_box2_broad_quarantined_KEPT.csv`
- supportive_box2_broad_quarantined_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_BROAD_QUARANTINE_202207_202606_supportive_box2_broad_quarantined_KEPT.csv`
- prevhealth_box2_prevhealth_broad_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_BROAD_QUARANTINE_202207_202606_prevhealth_box2_prevhealth_broad_KEPT.csv`
- control_supportive_box2_supportive_broad_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_BROAD_QUARANTINE_202207_202606_control_supportive_box2_supportive_broad_DROPPED.csv`
- prevhealth_box2_supportive_broad_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_BROAD_QUARANTINE_202207_202606_prevhealth_box2_supportive_broad_DROPPED.csv`
- prevhealth_box2_broad_quarantined_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_BROAD_QUARANTINE_202207_202606_prevhealth_box2_broad_quarantined_DROPPED.csv`
- supportive_box2_broad_quarantined_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_BROAD_QUARANTINE_202207_202606_supportive_box2_broad_quarantined_DROPPED.csv`
- prevhealth_box2_prevhealth_broad_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_BROAD_QUARANTINE_202207_202606_prevhealth_box2_prevhealth_broad_DROPPED.csv`
