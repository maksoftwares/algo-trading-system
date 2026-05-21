# Intrabar Ambiguity Report: trend_pullback

This report is generated from Phase 0 matrix trade CSVs. The engine uses the configured `adverse_first` policy when a bar touches both stop loss and take profit.

## Summary

- Trade files inspected: 9
- Total trades: 27576
- Ambiguous exit trades: 102 (0.37%)
- Same-timestamp entry/exit trades: 0 (0.00%)
- PF under adverse-first policy: 0.909566
- PF under neutral assumption: not_available_without_tick_or_replay_model
- PF under worst-case assumption: adverse_first_currently_used

## File Summary

| path | trade_count | ambiguous_exit_trades | same_timestamp_exit_trades | adverse_first_profit_factor |
| --- | --- | --- | --- | --- |
| C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase0/outputs/matrix_results/trend_pullback/cell_1_trend_pullback_capital_com_best_case_trades.csv | 3280 | 10 | 0 | 0.803836 |
| C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase0/outputs/matrix_results/trend_pullback/cell_2_trend_pullback_capital_com_median_trades.csv | 3280 | 10 | 0 | 0.803836 |
| C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase0/outputs/matrix_results/trend_pullback/cell_3_trend_pullback_capital_com_p95_trades.csv | 3280 | 10 | 0 | 0.749313 |
| C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase0/outputs/matrix_results/trend_pullback/cell_4_trend_pullback_pepperstone_best_case_trades.csv | 2873 | 14 | 0 | 0.936424 |
| C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase0/outputs/matrix_results/trend_pullback/cell_5_trend_pullback_pepperstone_median_trades.csv | 2873 | 14 | 0 | 0.936424 |
| C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase0/outputs/matrix_results/trend_pullback/cell_6_trend_pullback_pepperstone_p95_trades.csv | 2873 | 14 | 0 | 0.890875 |
| C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase0/outputs/matrix_results/trend_pullback/cell_7_trend_pullback_dukascopy_best_case_trades.csv | 3039 | 10 | 0 | 1.00686 |
| C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase0/outputs/matrix_results/trend_pullback/cell_8_trend_pullback_dukascopy_median_trades.csv | 3039 | 10 | 0 | 0.960589 |
| C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase0/outputs/matrix_results/trend_pullback/cell_9_trend_pullback_dukascopy_p95_trades.csv | 3039 | 10 | 0 | 0.866534 |

## Review Note

Neutral intrabar ordering is intentionally not inferred from OHLC bars. If this report shows material ambiguity, the next review step is tick-level replay or a separately specified neutral ordering simulator before Phase 1 approval.

CSV summary: outputs/reports/trend_pullback_intrabar_ambiguity_summary.csv
