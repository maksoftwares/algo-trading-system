# Phase 0R Estimate Report

Generated at UTC: 2026-06-02T19:05:17.806198Z
Measured cost applied: p95

Status: ESTIMATE_ONLY_NOT_PHASE0R_GATE

These results are draft estimates from existing processed bars. They are not Phase 0R promotion results, not paper-mode authorization, and not live-trading evidence.

Assumptions:

- Fixed risk for estimated P/L: $50.00 per 1R
- Execution: theoretical H4 close entry, H4 adverse-first stop/target simulation
- Target used for scoring: 1.5R
- Cost model: measured spread cost subtracted in R
- Overall rows dedupe repeated Phase 0 matrix cost-cell labels when the same measured cost is applied

## Overall Estimates

| candidate_id | trades | win_rate_pct | net_expectancy_R | total_net_R | estimated_net_PnL_USD | profit_factor | max_drawdown_R | median_stop_points | median_cost_R |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| d1_compression_h4_expansion_v0 | 4 | 50.00 | 0.3175 | 1.27 | 63.50 | 6.7382 | 0.21 | 29500.50 | 0.0082 |
| h4_trend_pullback_d1_bias_v0 | 0 | 0.00 | 0.0000 | 0.00 | 0.00 | n/a | 0.00 | 0.00 | 0.0000 |
| weekly_level_h4_rejection_v0 | 57 | 42.11 | -0.0766 | -4.36 | -218.20 | 0.8807 | 10.42 | 785.45 | 0.0955 |

## Cell Estimates

| candidate_id | cell | broker | period | trades | win_rate_pct | net_expectancy_R | total_net_R | profit_factor | max_drawdown_R |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| d1_compression_h4_expansion_v0 | 1 | capital_com | 2016-01-01 to 2018-12-31 | 0 | 0.00 | 0.0000 | 0.00 | n/a | 0.00 |
| d1_compression_h4_expansion_v0 | 2 | capital_com | 2016-01-01 to 2018-12-31 | 0 | 0.00 | 0.0000 | 0.00 | n/a | 0.00 |
| d1_compression_h4_expansion_v0 | 3 | capital_com | 2016-01-01 to 2018-12-31 | 0 | 0.00 | 0.0000 | 0.00 | n/a | 0.00 |
| d1_compression_h4_expansion_v0 | 4 | pepperstone | 2019-01-01 to 2021-12-31 | 2 | 50.00 | 0.7384 | 1.48 | 180.6705 | 0.01 |
| d1_compression_h4_expansion_v0 | 5 | pepperstone | 2019-01-01 to 2021-12-31 | 2 | 50.00 | 0.7384 | 1.48 | 180.6705 | 0.01 |
| d1_compression_h4_expansion_v0 | 6 | pepperstone | 2019-01-01 to 2021-12-31 | 2 | 50.00 | 0.7384 | 1.48 | 180.6705 | 0.01 |
| d1_compression_h4_expansion_v0 | 7 | dukascopy | 2022-01-01 to 2024-12-31 | 2 | 50.00 | -0.1034 | -0.21 | 0.0296 | 0.21 |
| d1_compression_h4_expansion_v0 | 8 | dukascopy | 2022-01-01 to 2024-12-31 | 2 | 50.00 | -0.1034 | -0.21 | 0.0296 | 0.21 |
| d1_compression_h4_expansion_v0 | 9 | dukascopy | 2022-01-01 to 2024-12-31 | 2 | 50.00 | -0.1034 | -0.21 | 0.0296 | 0.21 |
| h4_trend_pullback_d1_bias_v0 | 1 | capital_com | 2016-01-01 to 2018-12-31 | 0 | 0.00 | 0.0000 | 0.00 | n/a | 0.00 |
| h4_trend_pullback_d1_bias_v0 | 2 | capital_com | 2016-01-01 to 2018-12-31 | 0 | 0.00 | 0.0000 | 0.00 | n/a | 0.00 |
| h4_trend_pullback_d1_bias_v0 | 3 | capital_com | 2016-01-01 to 2018-12-31 | 0 | 0.00 | 0.0000 | 0.00 | n/a | 0.00 |
| h4_trend_pullback_d1_bias_v0 | 4 | pepperstone | 2019-01-01 to 2021-12-31 | 0 | 0.00 | 0.0000 | 0.00 | n/a | 0.00 |
| h4_trend_pullback_d1_bias_v0 | 5 | pepperstone | 2019-01-01 to 2021-12-31 | 0 | 0.00 | 0.0000 | 0.00 | n/a | 0.00 |
| h4_trend_pullback_d1_bias_v0 | 6 | pepperstone | 2019-01-01 to 2021-12-31 | 0 | 0.00 | 0.0000 | 0.00 | n/a | 0.00 |
| h4_trend_pullback_d1_bias_v0 | 7 | dukascopy | 2022-01-01 to 2024-12-31 | 0 | 0.00 | 0.0000 | 0.00 | n/a | 0.00 |
| h4_trend_pullback_d1_bias_v0 | 8 | dukascopy | 2022-01-01 to 2024-12-31 | 0 | 0.00 | 0.0000 | 0.00 | n/a | 0.00 |
| h4_trend_pullback_d1_bias_v0 | 9 | dukascopy | 2022-01-01 to 2024-12-31 | 0 | 0.00 | 0.0000 | 0.00 | n/a | 0.00 |
| weekly_level_h4_rejection_v0 | 1 | capital_com | 2016-01-01 to 2018-12-31 | 0 | 0.00 | 0.0000 | 0.00 | n/a | 0.00 |
| weekly_level_h4_rejection_v0 | 2 | capital_com | 2016-01-01 to 2018-12-31 | 0 | 0.00 | 0.0000 | 0.00 | n/a | 0.00 |
| weekly_level_h4_rejection_v0 | 3 | capital_com | 2016-01-01 to 2018-12-31 | 0 | 0.00 | 0.0000 | 0.00 | n/a | 0.00 |
| weekly_level_h4_rejection_v0 | 4 | pepperstone | 2019-01-01 to 2021-12-31 | 43 | 46.51 | 0.0187 | 0.80 | 1.0313 | 6.14 |
| weekly_level_h4_rejection_v0 | 5 | pepperstone | 2019-01-01 to 2021-12-31 | 43 | 46.51 | 0.0187 | 0.80 | 1.0313 | 6.14 |
| weekly_level_h4_rejection_v0 | 6 | pepperstone | 2019-01-01 to 2021-12-31 | 43 | 46.51 | 0.0187 | 0.80 | 1.0313 | 6.14 |
| weekly_level_h4_rejection_v0 | 7 | dukascopy | 2022-01-01 to 2024-12-31 | 14 | 28.57 | -0.3690 | -5.17 | 0.5274 | 5.47 |
| weekly_level_h4_rejection_v0 | 8 | dukascopy | 2022-01-01 to 2024-12-31 | 14 | 28.57 | -0.3690 | -5.17 | 0.5274 | 5.47 |
| weekly_level_h4_rejection_v0 | 9 | dukascopy | 2022-01-01 to 2024-12-31 | 14 | 28.57 | -0.3690 | -5.17 | 0.5274 | 5.47 |

## Trade Ledgers

- C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase0r\outputs\estimate_results\d1_compression_h4_expansion_v0_estimate_trades.csv
- C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase0r\outputs\estimate_results\h4_trend_pullback_d1_bias_v0_estimate_trades.csv
- C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase0r\outputs\estimate_results\weekly_level_h4_rejection_v0_estimate_trades.csv
