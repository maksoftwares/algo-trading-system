# Intrabar Ambiguity Report: round_number_retest_v0

This report is generated from Phase 0 matrix trade CSVs. The engine uses the configured `adverse_first` policy when a bar touches both stop loss and take profit.

## Summary

- Trade files inspected: 9
- Total trades: 47388
- Ambiguous exit trades: 198 (0.42%)
- Same-timestamp entry/exit trades: 0 (0.00%)
- PF under adverse-first policy: 1.47287
- PF under neutral assumption: not_available_without_tick_or_replay_model
- PF under worst-case assumption: adverse_first_currently_used

## File Summary

| path | trade_count | ambiguous_exit_trades | same_timestamp_exit_trades | adverse_first_profit_factor |
| --- | --- | --- | --- | --- |
| C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase0/outputs/matrix_results/round_number_retest_v0/cell_1_round_number_retest_v0_capital_com_best_case_trades.csv | 3837 | 18 | 0 | 1.48594 |
| C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase0/outputs/matrix_results/round_number_retest_v0/cell_2_round_number_retest_v0_capital_com_median_trades.csv | 3837 | 18 | 0 | 1.48594 |
| C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase0/outputs/matrix_results/round_number_retest_v0/cell_3_round_number_retest_v0_capital_com_p95_trades.csv | 3837 | 18 | 0 | 1.35122 |
| C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase0/outputs/matrix_results/round_number_retest_v0/cell_4_round_number_retest_v0_pepperstone_best_case_trades.csv | 5497 | 28 | 0 | 1.5596 |
| C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase0/outputs/matrix_results/round_number_retest_v0/cell_5_round_number_retest_v0_pepperstone_median_trades.csv | 5497 | 28 | 0 | 1.5596 |
| C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase0/outputs/matrix_results/round_number_retest_v0/cell_6_round_number_retest_v0_pepperstone_p95_trades.csv | 5497 | 28 | 0 | 1.47213 |
| C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase0/outputs/matrix_results/round_number_retest_v0/cell_7_round_number_retest_v0_dukascopy_best_case_trades.csv | 6462 | 20 | 0 | 1.46919 |
| C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase0/outputs/matrix_results/round_number_retest_v0/cell_8_round_number_retest_v0_dukascopy_median_trades.csv | 6462 | 20 | 0 | 1.46919 |
| C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase0/outputs/matrix_results/round_number_retest_v0/cell_9_round_number_retest_v0_dukascopy_p95_trades.csv | 6462 | 20 | 0 | 1.42093 |

## Review Note

Neutral intrabar ordering is intentionally not inferred from OHLC bars. If this report shows material ambiguity, the next review step is tick-level replay or a separately specified neutral ordering simulator before Phase 1 approval.

CSV summary: outputs/reports/round_number_retest_v0_intrabar_ambiguity_summary.csv
