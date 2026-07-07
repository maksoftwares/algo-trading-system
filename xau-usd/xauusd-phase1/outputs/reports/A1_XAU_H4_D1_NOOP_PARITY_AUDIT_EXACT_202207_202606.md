# A1 XAU H4/D1 No-Op Parity Audit Exact MT5

Generated UTC: `2026-07-07T11:26:07Z`

Scope: exact-MT5 no-op rerun of the two H4/D1 components, recomposed into the current F67-H16 no-f33 frontier. Both H4/D1 repair controls are disabled. This is an audit row, not a strategy improvement probe.

Status: `H4_D1_NOOP_PARITY_FAIL_STOP`
Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_H4_D1_NOOP_PARITY_AUDIT_PREREG_2026_07_07.md`
Preregistration SHA256: `9bea9b116385f609b020cccfc9c37e26f5b8efffe337a0a64dc988ac5b189f53`

## Headline Parity

| Variant | Signals | WR% | W/L | Active% | PF | Net | Stress -0.30 W/L | Positive weeks% | Worst week | Recent3 net | May net | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `baseline_f67_h16_no_f33` | 3751 | 50.23 | 2.0002 | 86.39 | 2.0336 | 22294.46 | 1.9029 | 54.81 | -878.18 | -1226.32 | -1055.98 | `BASELINE` |
| `noop_parity` | 3766 | 50.27 | 2.0177 | 86.48 | 2.0546 | 23025.01 | 1.9210 | 54.33 | -878.18 | -1226.32 | -1055.98 | `H4_D1_NOOP_PARITY_FAIL_STOP` |

## Deltas

| Metric | Delta |
| --- | ---: |
| `signals` | 15.0 |
| `wr_pp` | 0.04 |
| `wl` | 0.0175 |
| `active_pp` | 0.09 |
| `pf` | 0.021 |
| `net_usd` | 730.55 |
| `stress_030_wl` | 0.0181 |
| `positive_week_pp` | -0.48 |
| `worst_week_usd` | 0.0 |
| `recent3_net_usd` | 0.0 |
| `may_net_usd` | 0.0 |

## Pass-Fail Checks

- `signals_match`: `False`
- `net_within_0p01`: `False`
- `wr_within_0p01pp`: `False`
- `wl_within_0p0001`: `False`
- `active_within_0p01pp`: `False`
- `positive_weeks_within_0p01pp`: `False`
- `worst_week_within_0p01`: `True`
- `recent3_within_0p01`: `True`
- `may_within_0p01`: `True`
- `h4_d1_long_best_box2_atr80_signals_match`: `False`
- `h4_d1_long_best_box2_atr80_net_within_0p01`: `False`
- `h4_d1_long_broad_box3_atr60_signals_match`: `True`
- `h4_d1_long_broad_box3_atr60_net_within_0p01`: `True`

## H4/D1 Source Parity

| Source | Baseline signals | No-op signals | Baseline net | No-op net |
| --- | ---: | ---: | ---: | ---: |
| `h4_d1_long_best_box2_atr80` | 332 | 347 | 15613.96 | 16344.51 |
| `h4_d1_long_broad_box3_atr60` | 2 | 2 | 518.87 | 518.87 |

## MT5 Guard Counts

| Variant | Orders | h4_d1_supportive_state_guard | h4_d1_weekly_loss_governor | Other guard blocks |
| --- | ---: | ---: | ---: | ---: |
| `noop_parity_box2` | 633 | 0 | 0 | 270 |
| `noop_parity_broad` | 359 | 0 | 0 | 142 |

## Interpretation

No-op exact-MT5 rerun did not reproduce the baseline. Stop new source work until the drift is explained.

## Artifacts

- md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_D1_NOOP_PARITY_AUDIT_EXACT_202207_202606.md`
- json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_D1_NOOP_PARITY_AUDIT_EXACT_202207_202606.json`
- results_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_D1_NOOP_PARITY_AUDIT_EXACT_202207_202606_RESULTS.csv`
- kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_D1_NOOP_PARITY_AUDIT_EXACT_202207_202606_KEPT.csv`
- dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_D1_NOOP_PARITY_AUDIT_EXACT_202207_202606_DROPPED.csv`
- mt5_components_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_D1_NOOP_PARITY_AUDIT_EXACT_202207_202606_MT5_COMPONENTS.md`
- mt5_components_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_D1_NOOP_PARITY_AUDIT_EXACT_202207_202606_MT5_COMPONENTS.json`
