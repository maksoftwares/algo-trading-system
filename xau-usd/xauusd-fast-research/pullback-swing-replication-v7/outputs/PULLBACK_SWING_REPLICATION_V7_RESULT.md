# Pullback Swing Replication V7 Result

Decision: `V7_REJECTED`

| Window | Trades | Trades/day | Net USD | PF | DD USD | Top 5 removed | Positive months |
|---|---:|---:|---:|---:|---:|---:|---:|
| REVERSE_REPLICATION | 165 | 0.257 | -108.44 | 0.751 | 126.75 | -143.22 | 36.7% |
| DEVELOPMENT_1 | 288 | 0.367 | 149.84 | 1.208 | 68.62 | 62.84 | 50.0% |
| DEVELOPMENT_2 | 213 | 0.409 | 134.38 | 1.256 | 81.17 | 68.16 | 41.7% |
| CONFIRMATION_KNOWN | 150 | 0.575 | 327.59 | 1.833 | 53.95 | 240.97 | 50.0% |
| FINAL_KNOWN | 76 | 0.291 | 297.07 | 1.695 | 80.69 | 106.74 | 58.3% |

## Replication gates

- minimum_trades: **PASS**
- minimum_frequency: **PASS**
- minimum_profit_factor: **FAIL**
- positive_average_usd: **FAIL**
- positive_net_usd: **FAIL**
- maximum_closed_drawdown: **FAIL**
- top_winners_removed_positive: **FAIL**
- minimum_positive_month_share: **FAIL**
- long_direction: **FAIL**
- short_direction: **FAIL**
- bootstrap_lower_average_positive: **FAIL**

Month-cluster bootstrap 95% lower mean: **$-1.469/trade**.

This is historical reverse-time replication only. It does not authorize
model serving, EA consumption, demo trading, live trading, or broker action.
