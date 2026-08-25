# V60 V7 Profit-Protection Exemption V18 Result

Decision: **REJECT_KEEP_V60_AND_FROZEN_V6**

Historical exposed research only. No broker or deployment action is authorized.

| Metric | Deployed V60 | Frozen V6 | V18 | V18 vs V6 |
|---|---:|---:|---:|---:|
| Trades | 1390 | 1377 | 1375 | -2 |
| Net P/L | $3603.57 | $3681.34 | $3736.47 | $+55.13 |
| Profit factor | 1.7107 | 1.7377 | 1.7374 | -0.0003 |
| Closed drawdown | $223.28 | $217.46 | $218.71 | $+1.25 |
| Equity drawdown | $238.28 | $238.28 | $239.53 | $+1.25 |

## Mechanism exercise

- V7 exempt trade IDs observed: `370`.
- V7-only five-second cycles: `819797`.
- V7/non-V7 overlap cycles: `142653`.

## Gates

- `v6_floor_net_not_lower`: PASS
- `v6_floor_profit_factor_not_lower`: FAIL
- `v6_floor_closed_drawdown_not_higher`: FAIL
- `v6_floor_equity_drawdown_not_higher`: FAIL
- `v6_floor_3m_net_not_lower`: PASS
- `v6_floor_3m_profit_factor_not_lower`: PASS
- `v6_floor_6m_net_not_lower`: PASS
- `v6_floor_6m_profit_factor_not_lower`: PASS
- `v6_floor_12m_net_not_lower`: PASS
- `v6_floor_12m_profit_factor_not_lower`: PASS
- `v6_annual_2021_not_lower`: FAIL
- `v6_annual_2022_not_lower`: FAIL
- `v6_annual_2023_not_lower`: FAIL
- `v6_annual_2024_not_lower`: FAIL
- `v6_annual_2025_not_lower`: PASS
- `v6_annual_2026_not_lower`: PASS
- `trade_retention_vs_v60`: FAIL
- `frequency_retention_vs_v60`: FAIL
- `losing_month_burden_not_worse_v6`: FAIL
- `worst_month_not_worse_v6`: PASS
- `mechanism_exercised`: PASS
- `no_open_positions`: PASS
- `no_flat_deadlock`: PASS
- `no_floating_deadlock`: PASS
- `all_cost_stress_gates`: FAIL

## Evidence boundary

- July and August were not used as acceptance evidence.
- August V7 continuation is not evaluable because its frozen unprotected source endpoint is absent.
- A historical pass still requires clean Capital.com forward confirmation.
- V60 remains the only broker-action policy.
