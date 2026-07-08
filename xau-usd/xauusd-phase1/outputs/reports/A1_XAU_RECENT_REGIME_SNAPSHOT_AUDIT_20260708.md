# A1 XAU Recent Regime Snapshot Audit

Generated UTC: `2026-07-08T17:39:11Z`
Status: `R4_CHOP_SPECIALIST_NEXT`

Scope: exact-MT5 snapshot run using the EA-side Router V1 classifier. Snapshot mode logs regime state and returns before signal/trade logic.

## Summary

| Window | Bars | Active days | Dominant by bars | Bar share% | Dominant by days | Day share% |
| --- | ---: | ---: | --- | ---: | --- | ---: |
| `last_6_months_2026_01_01_to_2026_06_30` | 34655 | 153 | `chop` | 49.98 | `chop` | 50.98 |
| `last_3_months_2026_04_01_to_2026_06_30` | 17303 | 76 | `chop` | 59.15 | `chop` | 59.21 |

## last_6_months_2026_01_01_to_2026_06_30 Bar Distribution

| Regime | Bars | Bar % |
| --- | ---: | ---: |
| `shock` | 4920 | 14.20 |
| `uptrend` | 5094 | 14.70 |
| `downtrend` | 7320 | 21.12 |
| `compression` | 0 | 0.00 |
| `chop` | 17321 | 49.98 |
| `unknown` | 0 | 0.00 |

## last_6_months_2026_01_01_to_2026_06_30 Day Distribution

| Regime | Days | Day % |
| --- | ---: | ---: |
| `shock` | 20 | 13.07 |
| `uptrend` | 22 | 14.38 |
| `downtrend` | 33 | 21.57 |
| `compression` | 0 | 0.00 |
| `chop` | 78 | 50.98 |
| `unknown` | 0 | 0.00 |

## last_3_months_2026_04_01_to_2026_06_30 Bar Distribution

| Regime | Bars | Bar % |
| --- | ---: | ---: |
| `shock` | 396 | 2.29 |
| `uptrend` | 0 | 0.00 |
| `downtrend` | 6672 | 38.56 |
| `compression` | 0 | 0.00 |
| `chop` | 10235 | 59.15 |
| `unknown` | 0 | 0.00 |

## last_3_months_2026_04_01_to_2026_06_30 Day Distribution

| Regime | Days | Day % |
| --- | ---: | ---: |
| `shock` | 1 | 1.32 |
| `uptrend` | 0 | 0.00 |
| `downtrend` | 30 | 39.47 |
| `compression` | 0 | 0.00 |
| `chop` | 45 | 59.21 |
| `unknown` | 0 | 0.00 |

## Monthly Dominant Regime

| Period | Month | Dominant | Share% | Uptrend% | Downtrend% | Compression% | Chop% | Shock% |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `last_6_months_2026_01_01_to_2026_06_30` | 2026-01 | `uptrend` | 51.51 | 51.51 | 0.00 | 0.00 | 19.77 | 28.72 |
| `last_6_months_2026_01_01_to_2026_06_30` | 2026-02 | `shock` | 51.15 | 26.89 | 0.00 | 0.00 | 21.97 | 51.15 |
| `last_6_months_2026_01_01_to_2026_06_30` | 2026-03 | `chop` | 77.76 | 10.63 | 10.63 | 0.00 | 77.76 | 0.98 |
| `last_6_months_2026_01_01_to_2026_06_30` | 2026-04 | `chop` | 83.00 | 0.00 | 16.17 | 0.00 | 83.00 | 0.83 |
| `last_6_months_2026_01_01_to_2026_06_30` | 2026-05 | `chop` | 58.79 | 0.00 | 40.79 | 0.00 | 58.79 | 0.42 |
| `last_6_months_2026_01_01_to_2026_06_30` | 2026-06 | `downtrend` | 58.87 | 0.00 | 58.87 | 0.00 | 35.49 | 5.64 |
| `last_3_months_2026_04_01_to_2026_06_30` | 2026-04 | `chop` | 83.00 | 0.00 | 16.17 | 0.00 | 83.00 | 0.83 |
| `last_3_months_2026_04_01_to_2026_06_30` | 2026-05 | `chop` | 58.79 | 0.00 | 40.79 | 0.00 | 58.79 | 0.42 |
| `last_3_months_2026_04_01_to_2026_06_30` | 2026-06 | `downtrend` | 58.87 | 0.00 | 58.87 | 0.00 | 35.49 | 5.64 |

## Next Direction

Decision: `R4_CHOP_SPECIALIST_NEXT`

Recent market days are dominated by chop. Next test should be a range-fade or failed-break specialist with strict cost and top-winner robustness.

## Artifacts

- report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_RECENT_REGIME_SNAPSHOT_AUDIT_20260708.md`
- report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_RECENT_REGIME_SNAPSHOT_AUDIT_20260708.json`
- snapshots_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_RECENT_REGIME_SNAPSHOT_AUDIT_20260708_SNAPSHOTS.csv`
- period_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_RECENT_REGIME_SNAPSHOT_AUDIT_20260708_PERIOD_SUMMARY.csv`
- days_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_RECENT_REGIME_SNAPSHOT_AUDIT_20260708_DAYS.csv`
- weeks_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_RECENT_REGIME_SNAPSHOT_AUDIT_20260708_WEEKS.csv`
- months_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_RECENT_REGIME_SNAPSHOT_AUDIT_20260708_MONTHS.csv`
- hours_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_RECENT_REGIME_SNAPSHOT_AUDIT_20260708_HOURS.csv`
- mt5_report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_RECENT_REGIME_SNAPSHOT_AUDIT_20260708_MT5.md`
- mt5_report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_RECENT_REGIME_SNAPSHOT_AUDIT_20260708_MT5.json`
- mt5_signal_csv: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_recent_regime_snapshot_audit_202601_202606_20260701\A1XauM5Momentum_OWNER_GOAL_RECENT_REGIME_SNAPSHOT_AUDIT_202601_202606_XAUUSD_M5_recent_regime_snapshot_m5_signals.csv`
