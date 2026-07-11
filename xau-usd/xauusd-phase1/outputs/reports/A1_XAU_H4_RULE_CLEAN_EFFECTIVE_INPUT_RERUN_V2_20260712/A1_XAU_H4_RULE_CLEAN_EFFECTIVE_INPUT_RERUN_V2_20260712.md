# A1 XAUUSD H4 Rule-Clean Effective-Input Rerun V2

Status: `H4_RULE_CLEAN_UNDERPOWERED`

Research-only Strategy Tester evidence. No broker action is authorized.

| Horizon | Trades | WR% | PF | Net USD | Hard PF | Hard net | Native relative equity DD | Legacy blocks | Min-lot blocks |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `five_year` | 9 | 55.56 | 2.5434 | 122.56 | 2.1191 | 100.06 | 0.39% | 0 | 99 |
| `ten_year` | 36 | 55.56 | 2.5893 | 486.82 | 2.1458 | 396.82 | 0.69% | 0 | 120 |

## Failed survivor gates

- `ten_year_trades_ge_100`
- `best_24_month_lte_50pct`

## Boundary

A valid failure closes this H4 family under the current contract and does not authorize another repair. Zero native swap/fee is tester evidence only; documented Capital.com overnight funding remains required before promotion.
