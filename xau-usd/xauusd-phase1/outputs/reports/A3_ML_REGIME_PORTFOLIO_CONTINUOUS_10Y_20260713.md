# A3 ML Regime Portfolio Continuous Backtest

Status: `RESEARCH_GATES_FAIL`

This is exact-MT5 historical research, not a profit forecast or broker-action authorization.

## P/L Windows

| Window | Trades | WR% | Net USD | Stress net USD | PF | Stress PF | Max closed DD USD | Positive/active months |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `last_3_months` | 11 | 54.55 | 139.13 | 135.83 | 2.4928 | 2.4343 | 77.51 | 3/3 |
| `last_6_months` | 20 | 75.00 | 2812.28 | 2806.28 | 31.1747 | 30.6334 | 77.51 | 4/4 |
| `last_5_years` | 497 | 46.88 | 10975.60 | 10826.50 | 3.0137 | 2.9579 | 868.47 | 28/52 |
| `last_10_years` | 1056 | 42.61 | 12840.29 | 12523.49 | 2.4325 | 2.3694 | 868.47 | 48/101 |

## Drawdown Boundary

- Combined closed-trade drawdown: `$868.47`
- Largest component MT5 equity drawdown: `$1733.37`
- Conservative gate drawdown: `$1733.37`
- Nonnegative six-month blocks: `14/20` (70.00%)

## Regime Actions

- `R0_SHOCK`: `NO_TRADE`
- `R1_UPTREND`: `ARM_R1_LONG`
- `R2_DOWNTREND`: `ARM_R2_SHORT`
- `R3_COMPRESSION`: `NO_TRADE_NO_QUALIFIED_SPECIALIST`
- `R4_CHOP_UNDEFINED`: `NO_TRADE_NO_QUALIFIED_SPECIALIST`
- `TRANSITION`: `NO_TRADE`

## Gates

- `ten_year_stress_pf_ge_1p40`: PASS
- `last_3_months_stress_net_nonnegative`: PASS
- `last_6_months_stress_net_nonnegative`: PASS
- `conservative_drawdown_lte_1000`: FAIL
- `six_month_nonnegative_share_ge_75pct`: FAIL
- `only_frozen_r1_r2_sources`: PASS

## Evidence Boundary

All reported P/L is hypothetical historical fixed-lot P/L. All inspected history is development data. Demo/live action remains disabled.
