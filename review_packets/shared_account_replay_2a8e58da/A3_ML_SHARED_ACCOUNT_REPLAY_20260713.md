# A3 ML Shared-Account Portfolio Replay

Status: `RESEARCH_GATES_FAIL`

One-account historical research only. No demo or broker action is authorized.

## Baseline Versus Risk Control

| Profile | Accepted | Stress net USD | Stress PF | M5 equity DD USD | Max positions | Trades/market day |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Unconstrained | 1056 | 12523.49 | 2.3694 | 2171.41 | 14 | 0.4073 |
| Risk controlled | 705 | 4483.37 | 1.8603 | 694.68 | 3 | 0.2719 |

## Risk-Controlled Result

- Accepted/rejected candidates: `705/351`
- Ten-year net/stress net: `$4694.87` / `$4483.37`
- Ten-year PF/stress PF: `1.9237` / `1.8603`
- Trades per market day: `0.2719`
- Trades per active day: `1.8407`
- Positive active exit days: `43.98%`
- Shared M5 equity drawdown: `$694.68`
- Conservative drawdown: `$1733.37` (`17.33%` of initial balance)
- Maximum concurrent positions: `3`
- Opposite-direction overlap: `0.00` hours

## P/L Windows

| Window | Trades | Net USD | Stress net USD | Stress PF | Trades/market day | Worst day USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `last_3_months` | 11 | 139.13 | 135.83 | 2.4343 | 0.1719 | -21.60 |
| `last_6_months` | 13 | 784.82 | 780.92 | 9.2463 | 0.0942 | -21.60 |
| `last_5_years` | 329 | 3818.54 | 3719.84 | 2.2286 | 0.2523 | -177.78 |
| `last_10_years` | 705 | 4694.87 | 4483.37 | 1.8603 | 0.2719 | -177.78 |

## Component Calibration

- `r1_box_clean_strict_uptrend`: MT5 `$1733.37`, bar replay `$2170.21`, ratio `1.2520`: PASS
- `r2_pullback_short_h1_confirm`: MT5 `$270.01`, bar replay `$265.38`, ratio `0.9829`: PASS

## Ownership Audit

- Magic numbers unique: `FAIL`
- Collisions: `932200`

## Capital Boundary

- Fixed-lot capital for 10% observed drawdown: `$17333.70`
- Fixed-lot capital for 15% observed drawdown: `$11555.80`

## Gates

- `baseline_trade_count_reconciles`: PASS
- `baseline_net_pnl_reconciles`: PASS
- `unique_specialist_magic_numbers`: FAIL
- `component_equity_calibration`: PASS
- `ten_year_stress_pf_ge_minimum`: PASS
- `conservative_equity_drawdown_lte_limit`: FAIL
- `six_month_nonnegative_share_ge_minimum`: FAIL
- `risk_admission_limits_respected`: PASS
- `authorization_boundary_closed`: PASS

## Decision

Frequency remains a measured research gap. No entries were created or loosened to reach the target.
