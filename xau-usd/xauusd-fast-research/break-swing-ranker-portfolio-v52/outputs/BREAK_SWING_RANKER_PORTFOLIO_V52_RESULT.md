# XAUUSD Break-Swing Ranker Portfolio V52 Result

Decision: **V52_BREAK_SWING_RANKER_GATE_FAIL_TERMINAL**

Research only. V50 Core is unchanged and execution remains unauthorized.

| Window | Lane | Trades | Trades/day | Net USD | PF | Closed DD USD | Gate |
|---|---|---:|---:|---:|---:|---:|---|
| development | CORE | 209 | 0.267 | 170.92 | 1.481 | 36.78 |  |
| development | ADDON | 355 | 0.453 | 167.29 | 1.177 | 157.88 |  |
| development | COMBINED | 564 | 0.719 | 338.21 | 1.260 | 169.73 | DEVELOPMENT |
| validation | CORE | 356 | 0.683 | 749.77 | 1.731 | 252.68 |  |
| validation | ADDON | 261 | 0.501 | 427.34 | 1.759 | 89.98 |  |
| validation | COMBINED | 617 | 1.184 | 1177.11 | 1.741 | 161.70 | FAIL |
| final_exam | CORE | 365 | 0.699 | 3180.98 | 2.472 | 212.14 |  |
| final_exam | ADDON | 304 | 0.582 | 114.78 | 1.114 | 134.59 |  |
| final_exam | COMBINED | 669 | 1.282 | 3295.76 | 2.041 | 311.61 | FAIL |
| recent_tail | CORE | 138 | 0.529 | 1997.98 | 3.047 | 106.71 |  |
| recent_tail | ADDON | 132 | 0.506 | -101.92 | 0.824 | 122.61 |  |
| recent_tail | COMBINED | 270 | 1.034 | 1896.07 | 2.219 | 163.96 | FAIL |

## Failures

- `validation`: minimum_combined_positive_month_share
- `final_exam`: minimum_addon_profit_factor, addon_winner_removal_positive, maximum_combined_closed_drawdown
- `recent_tail`: minimum_addon_profit_factor, minimum_addon_net, addon_winner_removal_positive

## Interpretation

The fixed-action quarterly ranker failed at least one locked later-period frequency, marginal expectancy, stability, or drawdown gate. V52 is terminal and V50 remains the protected Core.

Whole-account floating drawdown remains unproven. No Python serving, EA, demo/live, or broker authority is granted.
