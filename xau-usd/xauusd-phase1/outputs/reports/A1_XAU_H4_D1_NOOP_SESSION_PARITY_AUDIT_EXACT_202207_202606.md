# A1 XAU H4/D1 No-Op Parity Audit Exact MT5

Generated UTC: `2026-07-07T11:36:09Z`

Scope: exact-MT5 no-op rerun of the two H4/D1 components, recomposed into the current F67-H16 no-f33 frontier. Both H4/D1 repair controls are disabled. Friday server-hour 20 is blocked to reproduce the archived baseline tester session that returned MT5 retcode 10018 market closed at those timestamps. This is an audit row, not a strategy improvement probe.

Status: `H4_D1_NOOP_SIGNAL_SHAPE_PARITY_PASS_MINOR_FILL_DRIFT`
Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_H4_D1_NOOP_PARITY_AUDIT_PREREG_2026_07_07.md`
Preregistration SHA256: `a2fe56683e950ea894c2b8d2f35c26585790fafa837d9f47e72a9c0b76dfbf45`

## Headline Parity

| Variant | Signals | WR% | W/L | Active% | PF | Net | Stress -0.30 W/L | Positive weeks% | Worst week | Recent3 net | May net | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `baseline_f67_h16_no_f33` | 3751 | 50.23 | 2.0002 | 86.39 | 2.0336 | 22294.46 | 1.9029 | 54.81 | -878.18 | -1226.32 | -1055.98 | `BASELINE` |
| `noop_parity` | 3751 | 50.23 | 1.9998 | 86.39 | 2.0333 | 22286.32 | 1.9025 | 54.81 | -878.18 | -1226.32 | -1055.98 | `H4_D1_NOOP_SIGNAL_SHAPE_PARITY_PASS_MINOR_FILL_DRIFT` |

## Deltas

| Metric | Delta |
| --- | ---: |
| `signals` | 0.0 |
| `wr_pp` | 0.0 |
| `wl` | -0.0004 |
| `active_pp` | 0.0 |
| `pf` | -0.0003 |
| `net_usd` | -8.14 |
| `stress_030_wl` | -0.0004 |
| `positive_week_pp` | 0.0 |
| `worst_week_usd` | 0.0 |
| `recent3_net_usd` | 0.0 |
| `may_net_usd` | 0.0 |

## Pass-Fail Checks

- `signals_match`: `True`
- `net_within_0p01`: `False`
- `wr_within_0p01pp`: `True`
- `wl_within_0p0001`: `False`
- `active_within_0p01pp`: `True`
- `positive_weeks_within_0p01pp`: `True`
- `worst_week_within_0p01`: `True`
- `recent3_within_0p01`: `True`
- `may_within_0p01`: `True`
- `h4_d1_long_best_box2_atr80_signals_match`: `True`
- `h4_d1_long_best_box2_atr80_net_within_0p01`: `False`
- `h4_d1_long_broad_box3_atr60_signals_match`: `True`
- `h4_d1_long_broad_box3_atr60_net_within_0p01`: `True`

## Signal-Shape Parity Checks

- `signals_match`: `True`
- `wr_within_0p01pp`: `True`
- `active_within_0p01pp`: `True`
- `positive_weeks_within_0p01pp`: `True`
- `worst_week_within_0p01`: `True`
- `recent3_within_0p01`: `True`
- `may_within_0p01`: `True`
- `net_fill_drift_within_10`: `True`
- `wl_fill_drift_within_0p0005`: `True`
- `h4_d1_long_best_box2_atr80_signals_match`: `True`
- `h4_d1_long_broad_box3_atr60_signals_match`: `True`
- `h4_box2_net_fill_drift_within_10`: `True`

## H4/D1 Source Parity

| Source | Baseline signals | No-op signals | Baseline net | No-op net |
| --- | ---: | ---: | ---: | ---: |
| `h4_d1_long_best_box2_atr80` | 332 | 332 | 15613.96 | 15605.82 |
| `h4_d1_long_broad_box3_atr60` | 2 | 2 | 518.87 | 518.87 |

## MT5 Guard Counts

| Variant | Orders | h4_d1_supportive_state_guard | h4_d1_weekly_loss_governor | Other guard blocks |
| --- | ---: | ---: | ---: | ---: |
| `noop_parity_box2` | 633 | 0 | 0 | 285 |
| `noop_parity_broad` | 359 | 0 | 0 | 152 |

## Interpretation

No-op exact-MT5 rerun reproduced signal count, source counts, weekly shape, recent 3M, and May 2026 after pinning the archived Friday 20:00 market-closed session. Strict cent-level parity still failed by a small MT5 fill drift (`-8.14 USD`, W/L `-0.0004`) across five old trades. Future repair comparisons should use this current no-op session-parity row as the comparison baseline for full-window dollars, while treating the archived baseline as valid for signal/weekly/recent-shape parity.

## Artifacts

- md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_D1_NOOP_SESSION_PARITY_AUDIT_EXACT_202207_202606.md`
- json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_D1_NOOP_SESSION_PARITY_AUDIT_EXACT_202207_202606.json`
- results_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_D1_NOOP_SESSION_PARITY_AUDIT_EXACT_202207_202606_RESULTS.csv`
- kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_D1_NOOP_SESSION_PARITY_AUDIT_EXACT_202207_202606_KEPT.csv`
- dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_D1_NOOP_SESSION_PARITY_AUDIT_EXACT_202207_202606_DROPPED.csv`
- mt5_components_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_D1_NOOP_SESSION_PARITY_AUDIT_EXACT_202207_202606_MT5_COMPONENTS.md`
- mt5_components_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_H4_D1_NOOP_SESSION_PARITY_AUDIT_EXACT_202207_202606_MT5_COMPONENTS.json`
