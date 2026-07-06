# A1 XAU Weekly Loss-Shape Repair Diagnostic - 2026-07-05

Status: `NO_CAUSAL_WEEKLY_REPAIR`

Scope: exact-ledger diagnostic only. No MT5 launch, live/demo runtime, chart, preset, order, position, or broker state was changed.

Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_WEEKLY_LOSS_SHAPE_REPAIR_DIAGNOSTIC_PREREG_2026_07_05.md`
Base kept ledger: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_HYBRID_F67_H16_NO_F33_COMPOSITION_202207_202606_KEPT.csv`

## Baseline Weekly Problem

| Signals | WR | W/L | Active | Positive Weeks | Worst Week | Net | June Net | June Worst Week |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 3751 | 50.23 | 2.0002 | 86.39 | 58.10 | -609.41 | 22294.46 | -222.84 | -522.85 |

## Best Causal Entry-Count Row

| Decision | Row | Signals | WR | W/L | Active | Positive Weeks | Worst Week | Net | June Net | June Worst Week |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `LOSS_SHAPE_IMPROVES_CORE_BREAKS` | `h4_max_1_per_week` | 3526 | 49.66 | 1.6008 | 86.10 | 61.90 | -285.81 | 9874.63 | 128.43 | -171.58 |

## Causal Rows

| Rank | Decision | Kind | Row | Signals | WR | W/L | Active | Positive Weeks | Worst Week | Net | June Net | June Worst Week |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `LOSS_SHAPE_IMPROVES_CORE_BREAKS` | `causal_entry_count` | `h4_max_1_per_week` | 3526 | 49.66 | 1.6008 | 86.10 | 61.90 | -285.81 | 9874.63 | 128.43 | -171.58 |
| 2 | `LOSS_SHAPE_IMPROVES_CORE_BREAKS` | `causal_entry_count` | `h4_max_1_per_day_and_1_per_week` | 3526 | 49.66 | 1.6008 | 86.10 | 61.90 | -285.81 | 9874.63 | 128.43 | -171.58 |
| 3 | `LOSS_SHAPE_IMPROVES_CORE_BREAKS` | `causal_entry_count` | `h4_max_2_per_day` | 3719 | 50.09 | 1.9504 | 86.39 | 58.57 | -609.41 | 20130.80 | -36.71 | -336.72 |
| 4 | `LOSS_SHAPE_IMPROVES_CORE_BREAKS` | `causal_entry_count` | `h4_max_1_per_day` | 3619 | 49.88 | 1.7851 | 86.39 | 58.57 | -466.40 | 14521.31 | 128.43 | -171.58 |
| 5 | `LOSS_SHAPE_IMPROVES_CORE_BREAKS` | `causal_entry_count` | `h4_max_1_per_day_and_3_per_week` | 3614 | 49.86 | 1.7750 | 86.39 | 58.57 | -466.40 | 14275.65 | 128.43 | -171.58 |
| 6 | `LOSS_SHAPE_IMPROVES_CORE_BREAKS` | `causal_entry_count` | `h4_max_2_per_week` | 3611 | 49.74 | 1.6993 | 86.29 | 59.05 | -428.82 | 13109.52 | -36.71 | -336.72 |
| 7 | `LOSS_SHAPE_IMPROVES_CORE_BREAKS` | `causal_entry_count` | `h4_max_2_per_day_and_2_per_week` | 3611 | 49.74 | 1.6993 | 86.29 | 59.05 | -428.82 | 13109.52 | -36.71 | -336.72 |
| 8 | `LOSS_SHAPE_IMPROVES_CORE_BREAKS` | `causal_entry_count` | `h4_max_1_per_day_and_2_per_week` | 3589 | 49.74 | 1.6968 | 86.39 | 58.57 | -466.40 | 12495.71 | 128.43 | -171.58 |

## Loss-Cap Sensitivity Rows

These rows are not executable claims and cannot justify promotion. They show how much loss geometry would need to change.

| Rank | Decision | Kind | Row | Signals | WR | W/L | Active | Positive Weeks | Worst Week | Net | June Net | June Worst Week |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `SENSITIVITY_ONLY_NOT_EXECUTABLE` | `sensitivity` | `all_loss_cap_50_sensitivity` | 3751 | 50.23 | 2.2086 | 86.39 | 59.05 | -244.77 | 24329.68 | 168.84 | -166.73 |
| 2 | `SENSITIVITY_ONLY_NOT_EXECUTABLE` | `sensitivity` | `h4_loss_cap_50_sensitivity` | 3751 | 50.23 | 2.2048 | 86.39 | 59.05 | -244.77 | 24296.75 | 168.84 | -166.73 |
| 3 | `SENSITIVITY_ONLY_NOT_EXECUTABLE` | `sensitivity` | `h4_loss_cap_75_sensitivity` | 3751 | 50.23 | 2.1250 | 86.39 | 58.10 | -281.10 | 23561.42 | 68.84 | -241.73 |
| 4 | `SENSITIVITY_ONLY_NOT_EXECUTABLE` | `sensitivity` | `all_loss_cap_75_sensitivity` | 3751 | 50.23 | 2.1250 | 86.39 | 58.10 | -281.10 | 23561.42 | 68.84 | -241.73 |
| 5 | `SENSITIVITY_ONLY_NOT_EXECUTABLE` | `sensitivity` | `h4_loss_cap_100_sensitivity` | 3751 | 50.23 | 2.0803 | 86.39 | 58.10 | -356.10 | 23124.82 | -16.72 | -316.73 |
| 6 | `SENSITIVITY_ONLY_NOT_EXECUTABLE` | `sensitivity` | `all_loss_cap_100_sensitivity` | 3751 | 50.23 | 2.0803 | 86.39 | 58.10 | -356.10 | 23124.82 | -16.72 | -316.73 |

## June Week Table

| Row | Week | Trades | Wins | Losses | Net |
|---|---|---:|---:|---:|---:|
| `baseline` | 2026-06-01 | 11 | 6 | 5 | 72.36 |
| `baseline` | 2026-06-08 | 8 | 6 | 2 | 196.81 |
| `baseline` | 2026-06-15 | 8 | 3 | 5 | -522.85 |
| `baseline` | 2026-06-22 | 12 | 7 | 5 | 30.84 |
| `baseline` | 2026-06-29 | 0 | 0 | 0 | 0.00 |
| `h4_max_1_per_week` | 2026-06-01 | 11 | 6 | 5 | 72.36 |
| `h4_max_1_per_week` | 2026-06-08 | 8 | 6 | 2 | 196.81 |
| `h4_max_1_per_week` | 2026-06-15 | 6 | 3 | 3 | -171.58 |
| `h4_max_1_per_week` | 2026-06-22 | 12 | 7 | 5 | 30.84 |
| `h4_max_1_per_week` | 2026-06-29 | 0 | 0 | 0 | 0.00 |
| `all_loss_cap_50_sensitivity` | 2026-06-01 | 11 | 6 | 5 | 72.36 |
| `all_loss_cap_50_sensitivity` | 2026-06-08 | 8 | 6 | 2 | 196.81 |
| `all_loss_cap_50_sensitivity` | 2026-06-15 | 8 | 3 | 5 | -166.73 |
| `all_loss_cap_50_sensitivity` | 2026-06-22 | 12 | 7 | 5 | 66.40 |
| `all_loss_cap_50_sensitivity` | 2026-06-29 | 0 | 0 | 0 | 0.00 |

## Interpretation

- Verdict: `NO_CAUSAL_WEEKLY_REPAIR`
- Causal H4/D1 entry-count caps are implementable in principle, but only qualify if they preserve the owner core metrics and materially improve weekly loss shape.
- Loss-cap rows are sensitivity-only; they point toward stop/risk geometry work, not a deployable rule.

## Artifacts

- JSON: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_WEEKLY_LOSS_SHAPE_REPAIR_DIAGNOSTIC_2026_07_05.json`
- CSV: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_WEEKLY_LOSS_SHAPE_REPAIR_DIAGNOSTIC_2026_07_05.csv`
- Best causal kept CSV: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_WEEKLY_LOSS_SHAPE_REPAIR_DIAGNOSTIC_2026_07_05_BEST_CAUSAL_KEPT.csv`
- June week CSV: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_WEEKLY_LOSS_SHAPE_REPAIR_DIAGNOSTIC_2026_07_05_JUNE_WEEK_TABLE.csv`
- Report: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_WEEKLY_LOSS_SHAPE_REPAIR_DIAGNOSTIC_2026_07_05.md`
