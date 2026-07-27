# V6 Causal Additive Replication V1 Result

Decision: **V6_CAUSAL_ADDITIVE_HISTORICAL_GATE_FAIL_QUARANTINED**

Historical research only. No trading execution is authorized.

## Standalone Accepted Candidate

- Trades: 213
- Stress net: $303.59
- Stress PF: 1.178
- Win rate: 34.7%
- Closed drawdown: $298.34

## Shared Account

- V60 trades: 2194
- Accepted V6 trades: 213
- Combined stress net: $5761.98
- Combined stress PF: 1.570
- Buffered floating drawdown: $426.89
- Maximum open add-ons: 3
- Maximum concurrent add-on risk: $65.54

## Required Windows

```csv
window,calendar_weekdays,baseline_trades,candidate_trades,combined_trades,baseline_stress_net_usd,candidate_stress_net_usd,combined_stress_net_usd,baseline_stress_profit_factor,candidate_stress_profit_factor,combined_stress_profit_factor,baseline_closed_drawdown_usd,candidate_closed_drawdown_usd,combined_closed_drawdown_usd,baseline_trades_per_weekday,combined_trades_per_weekday,candidate_winner_removed_stress_net_usd,daily_pnl_correlation,passed
development_2,521,595,112,707,1044.317,66.705,1111.022,1.584,1.107,1.460,248.027,162.246,264.973,1.142,1.357,-158.572,-0.049,False
confirmation,261,441,43,484,1223.652,87.429,1311.081,1.621,1.283,1.575,276.866,76.401,345.541,1.690,1.854,-137.518,0.243,False
final,261,364,33,397,2509.445,103.853,2613.298,1.960,1.165,1.806,208.414,298.339,230.115,1.395,1.521,-466.303,0.226,False
```

## Candidate By Entry Year

```csv
year,trades,win_rate_pct,stress_profit_factor,stress_net_usd,stress_closed_drawdown_usd
2022,59,37.288,1.225,71.560,71.724
2023,46,32.609,1.352,81.461,81.221
2024,53,33.962,0.827,-59.120,135.029
2025,40,35.000,1.126,57.602,120.428
2026,15,33.333,1.418,152.088,298.339
```

## Interpretation

This exact candidate is quarantined. It added historical net profit, but it failed preregistered robustness and shared-account risk gates. It must not be translated to MT5 or deployed.
