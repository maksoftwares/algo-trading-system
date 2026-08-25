# V60 R1 Monthly Quality Risk Overlay V16 Result

Decision: **RESEARCH_CHALLENGER_PASSES_FORWARD_CONFIRMATION_REQUIRED**

Research only. No deployment or broker action is authorized.

| Metric | V60 | V6 | V16 |
|---|---:|---:|---:|
| Trades | 1390 | 1377 | 1374 |
| Net P/L | $3603.57 | $3681.34 | $3721.79 |
| Profit factor | 1.7107 | 1.7377 | 1.7519 |
| Closed drawdown | $223.28 | $217.46 | $217.46 |
| Equity drawdown | $238.28 | $238.28 | $238.28 |
| Losing months | 21 | 20 | 20 |
| Losing-month P/L | $-527.82 | $-525.26 | $-492.21 |
| Worst month | $-136.77 | $-136.77 | $-120.70 |

Monthly-quality vetoes: `3`.

## Gates

- `baseline_trade_identity`: PASS
- `baseline_net_identity`: PASS
- `net_not_below_baseline`: PASS
- `profit_factor_not_below_baseline`: PASS
- `closed_drawdown_not_above_baseline`: PASS
- `equity_drawdown_not_above_baseline`: PASS
- `trade_retention`: PASS
- `frequency_retention`: PASS
- `no_negative_calendar_year_delta`: PASS
- `recent_windows_not_worse`: PASS
- `veto_cohort_large_enough`: PASS
- `veto_cohort_profit_factor_below_one`: PASS
- `v6_floor_net_not_lower`: PASS
- `v6_floor_profit_factor_not_lower`: PASS
- `v6_floor_closed_drawdown_not_higher`: PASS
- `v6_floor_equity_drawdown_not_higher`: PASS
- `v6_floor_3m_net_not_lower`: PASS
- `v6_floor_3m_profit_factor_not_lower`: PASS
- `v6_floor_6m_net_not_lower`: PASS
- `v6_floor_6m_profit_factor_not_lower`: PASS
- `v6_floor_12m_net_not_lower`: PASS
- `v6_floor_12m_profit_factor_not_lower`: PASS
- `v6_annual_floor_2021_pnl_not_lower`: PASS
- `v6_annual_floor_2022_pnl_not_lower`: PASS
- `v6_annual_floor_2023_pnl_not_lower`: PASS
- `v6_annual_floor_2024_pnl_not_lower`: PASS
- `v6_annual_floor_2025_pnl_not_lower`: PASS
- `v6_annual_floor_2026_pnl_not_lower`: PASS
- `negative_month_count_not_above_v6`: PASS
- `negative_month_pnl_better_than_v6`: PASS
- `worst_month_not_below_v6`: PASS
- `monthly_overlay_vetoes_present`: PASS
- `no_open_positions`: PASS
- `no_flat_deadlock`: PASS
- `no_floating_deadlock`: PASS
- `august_all_gates`: PASS
- `crossfeed_all_gates`: PASS
- `all_cost_stress_gates`: PASS

Clean forward evidence remains mandatory.
