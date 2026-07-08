# A1 XAU H4 Box2 Health Gate + Daily Stack Cap Exact MT5

Generated UTC: `2026-07-08T07:55:29Z`

Scope: one exact-MT5 H4/D1 box2 rerun with supportive guard, previous-month health gate, and max two entries per day; broad H4/D1 is quarantined. No live/demo runtime, chart, preset, order, position, or broker state was changed.

Status: `NO_H4_BOX2_DAILY_STACK_CAP_SURVIVOR`
Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_H4_BOX2_HEALTH_DAILY_STACK_CAP_EXACT_PREREG_2026_07_08.md`
Preregistration SHA256: `5ea746893ef0920db79ccdfe4e39e784053dd8c57bce3ff3c3e810866ed7f47a`

## Results

| Row | Decision | Signals | Blocked | WR% | W/L | Stress W/L | Active% | Net | Max DD | +Months | -Months | Pos weeks% | Worst month | Worst month net | Worst week |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| `prevhealth_box2_broad_quarantined` | `BASELINE` | 3934 | 0 | 49.08 | 2.1793 | 2.0507 | 87.44 | 20858.29 | 958.86 | 31 | 17 | 58.10 | `2023-02` | -405.08 | -878.18 |
| `prevhealth_box2_daily_stack_cap_broad_quarantined` | `REJECT_CORE_BREAK` | 3911 | 29 | 48.86 | 2.0546 | 1.9280 | 87.44 | 17942.30 | 683.45 | 31 | 17 | 58.10 | `2023-02` | -405.08 | -602.77 |

## Source Contributions

| Source | Signals | Net USD |
| --- | ---: | ---: |
| `freq_step3_frontier` | 3417 | 6127.72 |
| `h4_d1_long_best_box2_atr80` | 185 | 11433.58 |
| `short_hedge_v2_breakdown_retest` | 309 | 381.00 |

## MT5 Guard Counts

- Orders: `633`
- Daily max-trade blocks: `26`
- Previous-month health blocks: `17`
- Supportive-state blocks: `112`

## Interpretation

The daily stack cap broke the core candidate. Do not promote.

## Artifacts

- report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_DAILY_STACK_CAP_EXACT_202207_202606.md`
- report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_DAILY_STACK_CAP_EXACT_202207_202606.json`
- results_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_DAILY_STACK_CAP_EXACT_202207_202606_RESULTS.csv`
- kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_DAILY_STACK_CAP_EXACT_202207_202606_KEPT.csv`
- dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_DAILY_STACK_CAP_EXACT_202207_202606_DROPPED.csv`
- mt5_component_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_DAILY_STACK_CAP_EXACT_202207_202606_MT5_COMPONENT.md`
- mt5_component_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_BOX2_HEALTH_DAILY_STACK_CAP_EXACT_202207_202606_MT5_COMPONENT.json`
