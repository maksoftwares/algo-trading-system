# V60 Generic Source-Health Rank Veto V1 Result

Decision: **KEEP_DEPLOYED_V60**

Retrospective research only. No demo or live deployment is authorized.

| Metric | Deployed V60 | Challenger | Change |
|---|---:|---:|---:|
| Trades | 1390 | 1376 | -14 |
| Net P/L | $3603.57 | $3654.21 | $+50.64 |
| Profit factor | 1.7107 | 1.7292 | +0.0184 |
| Win rate | 48.49% | 48.84% | +0.35 pp |
| Closed drawdown | $223.28 | $217.46 | $-5.82 |
| Equity drawdown | $238.28 | $238.28 | $+0.00 |
| Trades/weekday | 0.970 | 0.960 | -0.010 |

Veto decisions: `14`; baseline-executed cohort: `14`. Baseline runtime PF: `0.13882546349190558`. Candidate endpoint PF: `0.09154221245595161`.

## Gates

- `baseline_trade_identity`: PASS
- `baseline_net_identity`: PASS
- `net_not_below_baseline`: PASS
- `profit_factor_not_below_baseline`: PASS
- `closed_drawdown_not_above_baseline`: PASS
- `equity_drawdown_not_above_baseline`: PASS
- `trade_retention`: FAIL
- `frequency_retention`: PASS
- `no_negative_calendar_year_delta`: PASS
- `recent_windows_not_worse`: PASS
- `veto_cohort_large_enough`: PASS
- `veto_cohort_profit_factor_below_one`: PASS
