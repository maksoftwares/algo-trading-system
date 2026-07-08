# A1 XAU Source-Level Monthly Firewall Diagnostic

Generated UTC: `2026-07-08T07:14:16Z`

Scope: causal source-level monthly firewall over existing exact-MT5 ledgers only. No MT5 launch, chart, preset, order, position, or broker state was changed.

Status: `NO_MONTHLY_FIREWALL_SURVIVOR`
Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_SOURCE_MONTHLY_FIREWALL_PREREG_2026_07_08.md`

## Best Rows

| Rank | Rule | Decision | Signals | Blocked | WR% | W/L | Stress W/L | Active% | Net | Max DD | +Months | -Months | Pos weeks% | Worst month | Worst month net | Worst week |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| 1 | `long_plus_short_v2_no_monthly_firewall` | `BASELINE` | 3953 | 0 | 49.00 | 2.1637 | 2.0390 | 87.54 | 21064.67 | 958.86 | 29 | 19 | 57.62 | `2023-02` | -405.08 | -878.18 |
| 2 | `baseline_supportive_guard_no_hedge` | `BASELINE` | 3645 | 0 | 50.40 | 2.0895 | 1.9720 | 85.71 | 20701.41 | 958.86 | 29 | 19 | 57.14 | `2023-02` | -392.46 | -878.18 |
| 3 | `h4_pnl_stop_50` | `REJECT_NO_MONTHLY_REPAIR` | 3927 | 26 | 48.89 | 2.1368 | 2.0092 | 87.44 | 19761.52 | 841.34 | 29 | 19 | 58.10 | `2023-02` | -405.08 | -475.52 |
| 4 | `h4_loss_count_stop_1` | `REJECT_NO_MONTHLY_REPAIR` | 3875 | 78 | 48.52 | 1.9715 | 1.8448 | 87.25 | 15627.25 | 841.34 | 29 | 19 | 57.62 | `2023-02` | -405.08 | -398.94 |
| 5 | `h4_loss_count_stop_3` | `REJECT_NO_MONTHLY_REPAIR` | 3949 | 4 | 49.05 | 2.1775 | 2.0515 | 87.54 | 21225.52 | 958.86 | 29 | 19 | 57.62 | `2023-02` | -405.08 | -878.18 |
| 6 | `h4_loss3_or_pnl150` | `REJECT_NO_MONTHLY_REPAIR` | 3949 | 4 | 49.05 | 2.1775 | 2.0515 | 87.54 | 21225.52 | 958.86 | 29 | 19 | 57.62 | `2023-02` | -405.08 | -878.18 |
| 7 | `h4_pnl_stop_100` | `REJECT_NO_MONTHLY_REPAIR` | 3953 | 0 | 49.00 | 2.1637 | 2.0390 | 87.54 | 21064.67 | 958.86 | 29 | 19 | 57.62 | `2023-02` | -405.08 | -878.18 |
| 8 | `h4_pnl_stop_150` | `REJECT_NO_MONTHLY_REPAIR` | 3953 | 0 | 49.00 | 2.1637 | 2.0390 | 87.54 | 21064.67 | 958.86 | 29 | 19 | 57.62 | `2023-02` | -405.08 | -878.18 |
| 9 | `h4_pnl_stop_200` | `REJECT_NO_MONTHLY_REPAIR` | 3953 | 0 | 49.00 | 2.1637 | 2.0390 | 87.54 | 21064.67 | 958.86 | 29 | 19 | 57.62 | `2023-02` | -405.08 | -878.18 |
| 10 | `freq_pnl_stop_200` | `REJECT_NO_MONTHLY_REPAIR` | 3953 | 0 | 49.00 | 2.1637 | 2.0390 | 87.54 | 21064.67 | 958.86 | 29 | 19 | 57.62 | `2023-02` | -405.08 | -878.18 |
| 11 | `h4_pnl150_freq_pnl200` | `REJECT_NO_MONTHLY_REPAIR` | 3953 | 0 | 49.00 | 2.1637 | 2.0390 | 87.54 | 21064.67 | 958.86 | 29 | 19 | 57.62 | `2023-02` | -405.08 | -878.18 |
| 12 | `freq_pnl_stop_150` | `REJECT_NO_MONTHLY_REPAIR` | 3935 | 18 | 49.05 | 2.1637 | 2.0391 | 87.34 | 21045.48 | 958.86 | 29 | 19 | 57.62 | `2023-02` | -405.08 | -878.18 |
| 13 | `h4_pnl100_freq_pnl150` | `REJECT_NO_MONTHLY_REPAIR` | 3935 | 18 | 49.05 | 2.1637 | 2.0391 | 87.34 | 21045.48 | 958.86 | 29 | 19 | 57.62 | `2023-02` | -405.08 | -878.18 |
| 14 | `h4_pnl_stop_75` | `REJECT_NO_MONTHLY_REPAIR` | 3939 | 14 | 48.92 | 2.1324 | 2.0080 | 87.44 | 20218.27 | 958.86 | 29 | 19 | 57.62 | `2023-02` | -405.08 | -878.18 |
| 15 | `h4_loss_count_stop_2` | `REJECT_NO_MONTHLY_REPAIR` | 3920 | 33 | 48.78 | 2.0939 | 1.9699 | 87.44 | 19123.21 | 958.86 | 29 | 19 | 58.10 | `2023-02` | -405.08 | -878.18 |
| 16 | `h4_loss2_or_pnl100` | `REJECT_NO_MONTHLY_REPAIR` | 3920 | 33 | 48.78 | 2.0939 | 1.9699 | 87.44 | 19123.21 | 958.86 | 29 | 19 | 58.10 | `2023-02` | -405.08 | -878.18 |
| 17 | `h4_loss2_or_pnl150` | `REJECT_NO_MONTHLY_REPAIR` | 3920 | 33 | 48.78 | 2.0939 | 1.9699 | 87.44 | 19123.21 | 958.86 | 29 | 19 | 58.10 | `2023-02` | -405.08 | -878.18 |
| 18 | `h4_loss2_or_pnl100_freq_pnl150` | `REJECT_NO_MONTHLY_REPAIR` | 3902 | 51 | 48.82 | 2.0938 | 1.9698 | 87.25 | 19104.02 | 958.86 | 29 | 19 | 58.10 | `2023-02` | -405.08 | -878.18 |
| 19 | `freq_pnl_stop_100` | `REJECT_NO_MONTHLY_REPAIR` | 3776 | 177 | 48.78 | 2.2140 | 2.0842 | 84.37 | 20277.61 | 879.05 | 27 | 21 | 55.24 | `2023-02` | -405.08 | -872.11 |
| 20 | `freq_pnl_stop_75` | `REJECT_NO_MONTHLY_REPAIR` | 3591 | 362 | 48.82 | 2.2458 | 2.1177 | 80.82 | 20181.63 | 879.05 | 27 | 21 | 52.86 | `2023-02` | -394.44 | -872.11 |

## Interpretation

Best row: `long_plus_short_v2_no_monthly_firewall` with `29` positive months, `19` negative months, net `21064.67`, and max closed drawdown `958.86`.

No source-level monthly firewall materially improved monthly consistency while preserving the profitable book.

## Artifacts

- report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SOURCE_MONTHLY_FIREWALL_202207_202606.md`
- report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SOURCE_MONTHLY_FIREWALL_202207_202606.json`
- results_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SOURCE_MONTHLY_FIREWALL_202207_202606_RESULTS.csv`
- best_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SOURCE_MONTHLY_FIREWALL_202207_202606_BEST_KEPT.csv`
- best_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SOURCE_MONTHLY_FIREWALL_202207_202606_BEST_DROPPED.csv`
