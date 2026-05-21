# Intrabar Ambiguity Report: range_mr

This report is generated from Phase 0 matrix trade CSVs. The engine uses the configured `adverse_first` policy when a bar touches both stop loss and take profit.

## Summary

- Trade files inspected: 9
- Total trades: 24
- Ambiguous exit trades: 0 (0.00%)
- Same-timestamp entry/exit trades: 0 (0.00%)
- PF under adverse-first policy: 0
- PF under neutral assumption: not_available_without_tick_or_replay_model
- PF under worst-case assumption: adverse_first_currently_used

## File Summary

| path | trade_count | ambiguous_exit_trades | same_timestamp_exit_trades | adverse_first_profit_factor |
| --- | --- | --- | --- | --- |
| C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase0/outputs/matrix_results/range_mr/cell_1_range_mr_capital_com_best_case_trades.csv | 3 | 0 | 0 | 0 |
| C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase0/outputs/matrix_results/range_mr/cell_2_range_mr_capital_com_median_trades.csv | 3 | 0 | 0 | 0 |
| C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase0/outputs/matrix_results/range_mr/cell_3_range_mr_capital_com_p95_trades.csv | 3 | 0 | 0 | 0 |
| C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase0/outputs/matrix_results/range_mr/cell_4_range_mr_pepperstone_best_case_trades.csv | 5 | 0 | 0 | 0 |
| C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase0/outputs/matrix_results/range_mr/cell_5_range_mr_pepperstone_median_trades.csv | 5 | 0 | 0 | 0 |
| C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase0/outputs/matrix_results/range_mr/cell_6_range_mr_pepperstone_p95_trades.csv | 5 | 0 | 0 | 0 |
| C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase0/outputs/matrix_results/range_mr/cell_7_range_mr_dukascopy_best_case_trades.csv | 0 | 0 | 0 | n/a |
| C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase0/outputs/matrix_results/range_mr/cell_8_range_mr_dukascopy_median_trades.csv | 0 | 0 | 0 | n/a |
| C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase0/outputs/matrix_results/range_mr/cell_9_range_mr_dukascopy_p95_trades.csv | 0 | 0 | 0 | n/a |

## Review Note

Neutral intrabar ordering is intentionally not inferred from OHLC bars. If this report shows material ambiguity, the next review step is tick-level replay or a separately specified neutral ordering simulator before Phase 1 approval.

CSV summary: outputs/reports/range_mr_intrabar_ambiguity_summary.csv
