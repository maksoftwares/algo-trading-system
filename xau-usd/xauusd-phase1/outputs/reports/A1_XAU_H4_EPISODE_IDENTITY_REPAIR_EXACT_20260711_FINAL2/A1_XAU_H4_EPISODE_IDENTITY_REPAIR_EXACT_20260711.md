# A1 XAUUSD H4 Episode-Identity Repair Exact-MT5 Results

Status: `H4_EPISODE_IDENTITY_REPAIR_FAILED`

Development data only; no broker action is authorized.

| Variant | Horizon | Currency | Trades | WR% | PF | Net | Max relative equity DD | Max positions | Session blocks | Min-lot blocks |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `structural_parity` | `five_year` | USD | 40 | 52.50 | 2.4048 | 1295.90 | 19.06% | 1 | 0 | 0 |
| `structural_parity` | `ten_year` | USD | 74 | 52.70 | 2.3996 | 1743.43 | 14.49% | 1 | 0 | 0 |
| `rule_clean_common_risk` | `five_year` | USD | 9 | 55.56 | 2.5434 | 122.56 | 0.39% | 1 | 1 | 97 |
| `rule_clean_common_risk` | `ten_year` | USD | 36 | 55.56 | 2.5893 | 486.82 | 0.69% | 1 | 1 | 118 |
| `small_aed_feasibility` | `five_year` | AED | 0 | 0.00 | 0.0000 | 0.00 | n/a | 0 | 1 | 106 |
| `small_aed_feasibility` | `ten_year` | AED | 0 | 0.00 | 0.0000 | 0.00 | n/a | 0 | 1 | 154 |

## Gates

- Structural parity: `False`
- Rule-clean common risk: `False`
- AED 3,672.50 feasibility: `False`

Native MT5 maximum relative equity drawdown is the controlling DD metric. Zero-trade small-account output is infeasibility, not success.
