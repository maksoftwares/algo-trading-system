# A1 XAU Portfolio Hedge Weekly Governor Diagnostic

Generated UTC: `2026-07-08T06:55:28Z`

Scope: causal weekly governor diagnostic over existing exact-MT5 ledgers only. No MT5 launch, chart, preset, order, position, or broker state was changed.

Status: `NO_PORTFOLIO_GOVERNOR_SURVIVOR`
Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_PORTFOLIO_HEDGE_WEEKLY_GOVERNOR_PREREG_2026_07_08.md`

## Best Rows

| Rank | Rule | Decision | Signals | Blocked | WR% | W/L | Stress W/L | Active% | Pos weeks% | Pos active weeks% | PF | Net | Worst week | Rolling 4w+% | June 2026 | Q2 2026 |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | `long_plus_short_v2_profit_lock_25` | `WEEKLY_IMPROVES_CORE_BREAKS` | 2341 | 1612 | 46.82 | 1.9868 | 1.8291 | 64.43 | 60.48 | 61.06 | 1.7589 | 6721.44 | -143.31 | 70.05 | 228.32 | 524.24 |
| 2 | `long_plus_short_v2_profit_lock_50` | `WEEKLY_IMPROVES_CORE_BREAKS` | 2698 | 1255 | 47.89 | 1.9525 | 1.8055 | 70.18 | 59.52 | 60.10 | 1.8070 | 8480.94 | -257.54 | 74.88 | 320.46 | 794.70 |
| 3 | `long_plus_short_v2_profit_lock_75` | `WEEKLY_IMPROVES_CORE_BREAKS` | 2944 | 1009 | 47.96 | 2.0069 | 1.8634 | 73.83 | 58.57 | 59.13 | 1.8606 | 10494.72 | -257.54 | 72.46 | 294.91 | 769.15 |
| 4 | `long_plus_short_v2_bracket_loss100_profit50` | `WEEKLY_IMPROVES_CORE_BREAKS` | 2659 | 1294 | 47.65 | 1.8735 | 1.7315 | 69.32 | 58.10 | 58.65 | 1.7176 | 7540.98 | -257.54 | 73.43 | 320.46 | 794.70 |
| 5 | `long_plus_short_v2_no_weekly_gate` | `BASELINE` | 3953 | 0 | 49.00 | 2.1637 | 2.0390 | 87.54 | 57.62 | 58.17 | 2.0934 | 21064.67 | -878.18 | 66.18 | 485.93 | 494.57 |
| 6 | `baseline_supportive_guard_no_hedge` | `BASELINE` | 3645 | 0 | 50.40 | 2.0895 | 1.9720 | 85.71 | 57.14 | 57.69 | 2.1395 | 20701.41 | -878.18 | 68.60 | 368.84 | 279.22 |
| 7 | `long_plus_short_v2_loss_stop_200` | `REJECT_NO_WEEKLY_REPAIR` | 3918 | 35 | 49.21 | 2.1560 | 2.0323 | 86.77 | 57.62 | 58.17 | 2.1036 | 21101.27 | -896.84 | 66.18 | 485.93 | 494.57 |
| 8 | `long_plus_short_v2_loss_stop_150` | `REJECT_NO_WEEKLY_REPAIR` | 3915 | 38 | 49.20 | 2.1547 | 2.0311 | 86.77 | 57.62 | 58.17 | 2.1013 | 21046.77 | -896.84 | 66.18 | 485.93 | 494.57 |
| 9 | `long_plus_short_v2_profit_lock_100` | `REJECT_NO_WEEKLY_REPAIR` | 3133 | 820 | 47.69 | 2.0039 | 1.8629 | 76.13 | 57.62 | 58.17 | 1.8367 | 11163.13 | -215.99 | 69.57 | 326.25 | 678.06 |
| 10 | `long_plus_short_v2_bracket_loss75_profit50` | `REJECT_NO_WEEKLY_REPAIR` | 2594 | 1359 | 47.73 | 1.8885 | 1.7447 | 68.17 | 57.62 | 58.17 | 1.7370 | 7456.01 | -257.54 | 72.46 | 320.46 | 794.70 |
| 11 | `long_plus_short_v2_profit_lock_150` | `REJECT_NO_WEEKLY_REPAIR` | 3326 | 627 | 47.84 | 1.9881 | 1.8543 | 78.52 | 57.14 | 57.69 | 1.8358 | 12211.41 | -257.54 | 65.70 | 383.30 | 542.07 |
| 12 | `long_plus_short_v2_bracket_loss100_profit75` | `REJECT_NO_WEEKLY_REPAIR` | 2883 | 1070 | 47.87 | 1.9555 | 1.8140 | 72.87 | 57.14 | 57.69 | 1.8062 | 9637.74 | -257.54 | 71.01 | 294.91 | 769.15 |
| 13 | `long_plus_short_v2_profit_lock_200` | `REJECT_NO_WEEKLY_REPAIR` | 3470 | 483 | 48.10 | 2.0291 | 1.8992 | 80.63 | 56.67 | 57.21 | 1.8941 | 14053.26 | -362.84 | 66.67 | 433.42 | 442.06 |
| 14 | `long_plus_short_v2_bracket_loss75_profit75` | `REJECT_NO_WEEKLY_REPAIR` | 2801 | 1152 | 48.02 | 1.9675 | 1.8244 | 71.24 | 56.67 | 57.21 | 1.8288 | 9496.23 | -257.54 | 71.01 | 294.91 | 769.15 |
| 15 | `long_plus_short_v2_bracket_loss50_profit50` | `REJECT_NO_WEEKLY_REPAIR` | 2412 | 1541 | 47.89 | 1.9114 | 1.7640 | 64.62 | 56.67 | 57.21 | 1.7704 | 7050.30 | -257.54 | 71.50 | 320.46 | 569.19 |
| 16 | `long_plus_short_v2_loss_stop_100` | `REJECT_NO_WEEKLY_REPAIR` | 3853 | 100 | 49.16 | 2.1385 | 2.0148 | 85.81 | 55.71 | 56.25 | 2.0824 | 20256.93 | -798.52 | 65.22 | 485.93 | 484.01 |
| 17 | `long_plus_short_v2_bracket_loss50_profit75` | `REJECT_NO_WEEKLY_REPAIR` | 2626 | 1327 | 48.13 | 1.9672 | 1.8203 | 67.79 | 55.71 | 56.25 | 1.8378 | 8702.63 | -257.54 | 71.98 | 294.91 | 543.64 |
| 18 | `long_plus_short_v2_loss_stop_75` | `REJECT_NO_WEEKLY_REPAIR` | 3753 | 200 | 49.21 | 2.1438 | 2.0203 | 83.70 | 55.24 | 55.77 | 2.0928 | 19892.31 | -798.52 | 65.22 | 485.93 | 500.00 |
| 19 | `long_plus_short_v2_bracket_loss100_profit150` | `REJECT_NO_WEEKLY_REPAIR` | 3251 | 702 | 47.77 | 1.9425 | 1.8100 | 77.18 | 55.24 | 55.77 | 1.7893 | 11245.85 | -257.54 | 65.22 | 383.30 | 531.51 |
| 20 | `long_plus_short_v2_bracket_loss100_profit100` | `REJECT_NO_WEEKLY_REPAIR` | 3089 | 864 | 47.39 | 1.9328 | 1.7963 | 75.26 | 55.24 | 55.77 | 1.7510 | 10068.98 | -215.99 | 67.63 | 326.25 | 667.50 |

## Interpretation

Best row: `long_plus_short_v2_profit_lock_25` with `60.48%` positive calendar weeks, `46.82%` WR, `1.9868` W/L, and `6721.44` net.

The weekly governor grid did not produce a useful repair. The blocker is not just week-level trade stopping; the portfolio still needs a genuinely smoother independent source or a relaxed weekly target.

## Artifacts

- report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_PORTFOLIO_HEDGE_WEEKLY_GOVERNOR_202207_202606.md`
- report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_PORTFOLIO_HEDGE_WEEKLY_GOVERNOR_202207_202606.json`
- results_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_PORTFOLIO_HEDGE_WEEKLY_GOVERNOR_202207_202606_RESULTS.csv`
- best_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_PORTFOLIO_HEDGE_WEEKLY_GOVERNOR_202207_202606_BEST_KEPT.csv`
- best_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_PORTFOLIO_HEDGE_WEEKLY_GOVERNOR_202207_202606_BEST_DROPPED.csv`
