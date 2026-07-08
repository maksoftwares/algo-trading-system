# A1 XAU Realistic Candidate Monthly Health

Generated UTC: `2026-07-08T12:22:14Z`
Status: `REALISTIC_MONTHLY_HEALTH_NO_SURVIVOR`

Scope: causal previous-month source-health gate on the current chart-context long/short blend. No MT5 launch, live/demo runtime, chart, preset, order, position, or broker state was changed.

Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_REALISTIC_CANDIDATE_MONTHLY_HEALTH_PREREG_2026_07_08.md`
Preregistration SHA256: `7a50d6e53079562ca2dfa665d1d3b8a1600d63fbe1aa4240197ab85d8b6f67e1`

## Baseline

| Signals | WR% | W/L | Stress W/L | Active% | Net | Max DD | +Months | -Months | Pos weeks% | Q2 | Recent3 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3794 | 50.03 | 2.1328 | 2.0084 | 86.58 | 20882.42 | 958.86 | 31 | 17 | 58.57 | 514.04 | 514.04 |

## Results

| Variant | Decision | Dropped | Dropped net | WR% | W/L | Stress W/L | Net | Net delta | Max DD | DD delta | +Months | -Months | Pos weeks% | Week delta | Q2 | Recent3 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `freq_only_prev_month_health` | `REJECT_REALISTIC_GATE` | 783 | 1304.73 | 49.75 | 2.2549 | 2.1367 | 19577.69 | -1304.73 | 958.86 | 0.00 | 30 | 17 | 51.90 | -6.67 | 145.20 | 145.20 |
| `short_only_prev_month_health` | `REJECT_REALISTIC_GATE` | 13 | -14.49 | 50.12 | 2.1278 | 2.0040 | 20896.91 | 14.49 | 958.86 | 0.00 | 31 | 17 | 58.57 | 0.00 | 514.04 | 514.04 |
| `freq_and_short_prev_month_health` | `REJECT_REALISTIC_GATE` | 796 | 1290.24 | 49.87 | 2.2482 | 2.1307 | 19592.18 | -1290.24 | 958.86 | 0.00 | 30 | 17 | 51.90 | -6.67 | 145.20 | 145.20 |
| `all_sources_prev_month_health` | `REJECT_REALISTIC_GATE` | 822 | 5294.93 | 49.46 | 2.0287 | 1.9177 | 15587.49 | -5294.93 | 958.86 | 0.00 | 30 | 17 | 51.43 | -7.14 | 145.20 | 145.20 |

## Gate Failures

- `freq_only_prev_month_health`: wr_ge_50, active_ge_84, positive_months_ge_32, negative_months_le_16, positive_weeks_not_worse
- `short_only_prev_month_health`: positive_months_ge_32, negative_months_le_16
- `freq_and_short_prev_month_health`: wr_ge_50, active_ge_84, positive_months_ge_32, negative_months_le_16, positive_weeks_not_worse
- `all_sources_prev_month_health`: wr_ge_50, net_ge_19000, active_ge_84, positive_months_ge_32, negative_months_le_16, positive_weeks_not_worse

## Best Source Contributions

| Source | Signals | Net USD |
| --- | ---: | ---: |
| `freq_step3_frontier` | 3416 | 6134.72 |
| `h4_d1_long_best_box2_atr80` | 208 | 14349.57 |
| `short_v4_impulse_retest_d1_structural_h1h4` | 157 | 412.62 |

## Interpretation

No previous-month source-health row passed all realistic gates. Best diagnostic was `short_only_prev_month_health` with 31 positive months, WR 50.12%, net 20896.91, and DD delta 0.00. The current chart-context blend remains the best review candidate.

## Artifacts

- report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_REALISTIC_CANDIDATE_MONTHLY_HEALTH_20260708.md`
- report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_REALISTIC_CANDIDATE_MONTHLY_HEALTH_20260708.json`
- results_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_REALISTIC_CANDIDATE_MONTHLY_HEALTH_20260708_RESULTS.csv`
- best_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_REALISTIC_CANDIDATE_MONTHLY_HEALTH_20260708_short_only_prev_month_health_KEPT.csv`
- best_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_REALISTIC_CANDIDATE_MONTHLY_HEALTH_20260708_short_only_prev_month_health_DROPPED.csv`
