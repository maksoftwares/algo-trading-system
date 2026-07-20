# XAUUSD One-Trade-Per-Day Portfolio V51 Result

Decision: **V51_ONE_TRADE_PER_DAY_HISTORICAL_GATE_FAIL_TERMINAL**

Research only. V50 Core is unchanged; no prediction, EA, demo/live, or broker action is authorized.

## Chronological results

| Window | Lane | Trades | Trades/day | Net USD | PF | Closed DD USD | Gate |
|---|---|---:|---:|---:|---:|---:|---|
| development | CORE | 209 | 0.267 | 170.92 | 1.481 | 36.78 |  |
| development | ADDON | 735 | 0.938 | 186.96 | 1.202 | 120.05 |  |
| development | COMBINED | 944 | 1.204 | 357.88 | 1.280 | 99.86 | DEVELOPMENT |
| validation | CORE | 356 | 0.683 | 749.77 | 1.731 | 252.68 |  |
| validation | ADDON | 490 | 0.940 | 395.92 | 1.511 | 78.74 |  |
| validation | COMBINED | 846 | 1.624 | 1145.69 | 1.636 | 196.31 | FAIL |
| final_exam | CORE | 365 | 0.699 | 3180.98 | 2.472 | 212.14 |  |
| final_exam | ADDON | 542 | 1.038 | -235.04 | 0.862 | 532.50 |  |
| final_exam | COMBINED | 907 | 1.738 | 2945.94 | 1.763 | 313.60 | FAIL |
| recent_tail | CORE | 138 | 0.529 | 1997.98 | 3.047 | 106.71 |  |
| recent_tail | ADDON | 203 | 0.778 | -422.02 | 0.545 | 422.02 |  |
| recent_tail | COMBINED | 341 | 1.307 | 1575.97 | 1.828 | 165.24 | FAIL |

## Gate failures

- `validation`: minimum_combined_positive_month_share
- `final_exam`: minimum_addon_profit_factor, minimum_addon_net, maximum_addon_drawdown, addon_winner_removal_positive, maximum_combined_closed_drawdown
- `recent_tail`: minimum_addon_profit_factor, minimum_addon_net, maximum_addon_drawdown, addon_winner_removal_positive

## Risk interpretation

Maximum observed combined closed drawdown was USD 313.60; after the 25% buffer it is USD 391.99.
Whole-account floating equity drawdown remains unproven because every historical Core specialist lacks intratrade marks. Execution therefore remains fail-closed.

## Interpretation

The fixed add-on did not satisfy every locked later-period frequency, expectancy, stability, and drawdown gate. V51 is terminal and must not be repaired after opening these outcomes; V50 remains the protected Core.
