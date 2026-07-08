# A1 XAU Previous-Month Source Health Gate Diagnostic

Generated UTC: `2026-07-08T07:16:58Z`

Scope: causal previous-month source-health gates over existing exact-MT5 ledgers only. No MT5 launch, chart, preset, order, position, or broker state was changed.

Status: `SOURCE_HEALTH_WATCHLIST`
Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_PREVIOUS_MONTH_SOURCE_HEALTH_GATE_PREREG_2026_07_08.md`

## Best Rows

| Rank | Rule | Decision | Signals | Blocked | WR% | W/L | Stress W/L | Active% | Net | Max DD | +Months | -Months | Pos weeks% | Worst month | Worst month net |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| 1 | `h4_prev1_net_lt_50` | `SOURCE_HEALTH_WATCHLIST` | 3936 | 17 | 49.11 | 2.2056 | 2.0761 | 87.44 | 21377.16 | 958.86 | 31 | 17 | 58.10 | `2023-02` | -405.08 |
| 2 | `h4_prev1_losses_ge_1` | `MONTHLY_IMPROVES_CORE_BREAKS` | 3853 | 100 | 48.66 | 1.7981 | 1.6765 | 87.25 | 12631.48 | 958.86 | 32 | 16 | 59.52 | `2022-08` | -145.37 |
| 3 | `h4_prev1_net_lt_1` | `MONTHLY_IMPROVES_CORE_BREAKS` | 3908 | 45 | 48.77 | 1.9858 | 1.8636 | 87.34 | 16853.60 | 958.86 | 31 | 17 | 57.62 | `2023-02` | -405.08 |
| 4 | `h4_prev1_net_lt_25` | `MONTHLY_IMPROVES_CORE_BREAKS` | 3908 | 45 | 48.77 | 1.9858 | 1.8636 | 87.34 | 16853.60 | 958.86 | 31 | 17 | 57.62 | `2023-02` | -405.08 |
| 5 | `h4_prev2_net_lt_25` | `MONTHLY_IMPROVES_CORE_BREAKS` | 3853 | 100 | 48.27 | 1.8337 | 1.7137 | 87.34 | 13144.67 | 958.86 | 31 | 17 | 57.14 | `2023-02` | -405.08 |
| 6 | `h4_prev2_net_lt_50` | `MONTHLY_IMPROVES_CORE_BREAKS` | 3853 | 100 | 48.27 | 1.8337 | 1.7137 | 87.34 | 13144.67 | 958.86 | 31 | 17 | 57.14 | `2023-02` | -405.08 |
| 7 | `h4_prev1_losses_ge_2` | `MONTHLY_IMPROVES_CORE_BREAKS` | 3867 | 86 | 48.54 | 1.7812 | 1.6631 | 87.25 | 12538.39 | 958.86 | 31 | 17 | 59.05 | `2023-02` | -188.44 |
| 8 | `h4_prev2_net_lt_100` | `MONTHLY_IMPROVES_CORE_BREAKS` | 3879 | 74 | 48.62 | 2.0660 | 1.9380 | 87.34 | 17628.51 | 958.86 | 30 | 18 | 57.14 | `2023-02` | -405.08 |
| 9 | `h4_prev1_losses_ge_3` | `MONTHLY_IMPROVES_CORE_BREAKS` | 3914 | 39 | 48.85 | 2.0030 | 1.8808 | 87.34 | 17344.67 | 958.86 | 30 | 18 | 58.10 | `2023-02` | -315.44 |
| 10 | `long_plus_short_v2_no_source_health_gate` | `BASELINE` | 3953 | 0 | 49.00 | 2.1637 | 2.0390 | 87.54 | 21064.67 | 958.86 | 29 | 19 | 57.62 | `2023-02` | -405.08 |
| 11 | `h4_prev1_net_lt_75` | `REJECT_NO_MONTHLY_REPAIR` | 3939 | 14 | 49.07 | 2.1917 | 2.0636 | 87.44 | 21230.42 | 958.86 | 30 | 18 | 57.62 | `2023-02` | -405.08 |
| 12 | `h4_prev1_net_lt_150` | `REJECT_NO_MONTHLY_REPAIR` | 3947 | 6 | 49.02 | 2.1835 | 2.0564 | 87.44 | 21164.20 | 958.86 | 29 | 19 | 57.62 | `2023-02` | -405.08 |
| 13 | `h4_prev1_net_lt_200` | `REJECT_NO_MONTHLY_REPAIR` | 3947 | 6 | 49.02 | 2.1835 | 2.0564 | 87.44 | 21164.20 | 958.86 | 29 | 19 | 57.62 | `2023-02` | -405.08 |
| 14 | `h4_prev1_losses_ge_10` | `REJECT_NO_MONTHLY_REPAIR` | 3953 | 0 | 49.00 | 2.1637 | 2.0390 | 87.54 | 21064.67 | 958.86 | 29 | 19 | 57.62 | `2023-02` | -405.08 |
| 15 | `freq_prev1_net_lt_150` | `REJECT_NO_MONTHLY_REPAIR` | 3953 | 0 | 49.00 | 2.1637 | 2.0390 | 87.54 | 21064.67 | 958.86 | 29 | 19 | 57.62 | `2023-02` | -405.08 |
| 16 | `freq_prev1_net_lt_200` | `REJECT_NO_MONTHLY_REPAIR` | 3953 | 0 | 49.00 | 2.1637 | 2.0390 | 87.54 | 21064.67 | 958.86 | 29 | 19 | 57.62 | `2023-02` | -405.08 |
| 17 | `h4_prev1_net_lt_100` | `REJECT_NO_MONTHLY_REPAIR` | 3941 | 12 | 49.00 | 2.1782 | 2.0509 | 87.44 | 20949.14 | 958.86 | 29 | 19 | 57.14 | `2023-02` | -405.08 |
| 18 | `freq_prev2_net_lt_100` | `REJECT_NO_MONTHLY_REPAIR` | 3868 | 85 | 49.02 | 2.1987 | 2.0713 | 86.86 | 20923.99 | 958.86 | 29 | 19 | 57.62 | `2023-02` | -405.08 |
| 19 | `freq_prev1_net_lt_100` | `REJECT_NO_MONTHLY_REPAIR` | 3902 | 51 | 48.95 | 2.1712 | 2.0457 | 86.10 | 20766.22 | 958.86 | 29 | 19 | 56.67 | `2023-02` | -405.08 |
| 20 | `freq_prev2_net_lt_50` | `REJECT_NO_MONTHLY_REPAIR` | 3641 | 312 | 48.59 | 2.2297 | 2.1012 | 83.13 | 19505.18 | 958.86 | 29 | 19 | 56.19 | `2023-02` | -405.08 |

## Interpretation

Best row: `h4_prev1_net_lt_50` with `31` positive months, `17` negative months, net `21377.16`, and max closed drawdown `958.86`.

A previous-month source-health gate improved monthly consistency while preserving the profitable core. This is the next exact-MT5 implementation candidate.

## Artifacts

- report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_PREVIOUS_MONTH_SOURCE_HEALTH_GATE_202207_202606.md`
- report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_PREVIOUS_MONTH_SOURCE_HEALTH_GATE_202207_202606.json`
- results_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_PREVIOUS_MONTH_SOURCE_HEALTH_GATE_202207_202606_RESULTS.csv`
- best_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_PREVIOUS_MONTH_SOURCE_HEALTH_GATE_202207_202606_BEST_KEPT.csv`
- best_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_PREVIOUS_MONTH_SOURCE_HEALTH_GATE_202207_202606_BEST_DROPPED.csv`
