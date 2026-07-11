# A1 XAU R5 Pre-Downtrend Break Short V1 Exact-MT5

Generated UTC: `2026-07-11T14:05:09Z`
Status: `R5_STANDALONE_FAIL`

Boundary: development Strategy Tester only. No broker action is authorized.

Currency note: Raw shared-parser fields named profit_aed or pnl_aed contain tester-currency USD values in this packet; the names are retained only for backward-compatible schema consumption.

| Horizon | Trades | WR% | W/L | PF | Net USD | Stress PF | Stress net | Native equity DD% | History | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `five_year` | 412 | 27.91 | 1.9572 | 0.7578 | -317.65 | 0.6850 | -441.25 | 34.96 | 98.00% | False |
| `ten_year` | 612 | 28.92 | 1.9635 | 0.7990 | -380.64 | 0.7212 | -564.24 | 44.09 | 98.00% | False |

## Robustness and independence

- Early five-year half net: `-62.99` USD.
- Late five-year half net: `-317.65` USD.
- Positive exact annual buckets: `2 / 10`.
- Top ten winning trades removed: `-548.85` USD.
- Top three winning entry days removed: `-434.46` USD.
- Daily closed-P/L correlation with H4: `-0.008052`.
- Common-window H4 episodes touched: `13 / 13`.
- Full-decade H4 episodes touched: `33 / 39`.

## Failed gates

- `five_year::net_profit_gt_0`
- `five_year::win_rate_ge_40pct`
- `five_year::profit_factor_ge_1p30`
- `five_year::native_relative_equity_dd_lte_12pct`
- `five_year::stress_030_net_gt_0`
- `five_year::stress_030_pf_ge_1p20`
- `ten_year::net_profit_gt_0`
- `ten_year::win_rate_ge_40pct`
- `ten_year::profit_factor_ge_1p30`
- `ten_year::native_relative_equity_dd_lte_12pct`
- `ten_year::stress_030_net_gt_0`
- `ten_year::stress_030_pf_ge_1p20`
- `robustness::early_five_year_half_nonnegative`
- `robustness::late_five_year_half_nonnegative`
- `robustness::at_least_seven_of_ten_annual_buckets_positive`
- `robustness::top10_winning_trades_removed_net_positive`
- `robustness::top3_winning_entry_days_removed_net_positive`

## Boundary

This is one preregistered cell, not an optimization sweep. A standalone failure is not rescued by portfolio composition.
No runtime chart, preset, account, order, or broker state is changed by this runner.
