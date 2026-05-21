# Intrabar Ambiguity Report: breakout_retest

This report is generated from Phase 0 matrix trade CSVs. The engine uses the configured `adverse_first` policy when a bar touches both stop loss and take profit.

## Summary

- Trade files inspected: 9
- Total trades: 66759
- Ambiguous exit trades: 525 (0.79%)
- Same-timestamp entry/exit trades: 0 (0.00%)
- PF under adverse-first policy: 1.46574
- PF under neutral assumption: not_available_without_tick_or_replay_model
- PF under worst-case assumption: adverse_first_currently_used

## File Summary

| path | trade_count | ambiguous_exit_trades | same_timestamp_exit_trades | adverse_first_profit_factor |
| --- | --- | --- | --- | --- |
| C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase0/outputs/matrix_results/breakout_retest/cell_1_breakout_retest_capital_com_best_case_trades.csv | 7287 | 41 | 0 | 1.41196 |
| C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase0/outputs/matrix_results/breakout_retest/cell_2_breakout_retest_capital_com_median_trades.csv | 7287 | 41 | 0 | 1.41196 |
| C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase0/outputs/matrix_results/breakout_retest/cell_3_breakout_retest_capital_com_p95_trades.csv | 7287 | 41 | 0 | 1.25507 |
| C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase0/outputs/matrix_results/breakout_retest/cell_4_breakout_retest_pepperstone_best_case_trades.csv | 7174 | 47 | 0 | 1.30566 |
| C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase0/outputs/matrix_results/breakout_retest/cell_5_breakout_retest_pepperstone_median_trades.csv | 7174 | 47 | 0 | 1.30566 |
| C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase0/outputs/matrix_results/breakout_retest/cell_6_breakout_retest_pepperstone_p95_trades.csv | 7174 | 47 | 0 | 1.23335 |
| C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase0/outputs/matrix_results/breakout_retest/cell_7_breakout_retest_dukascopy_best_case_trades.csv | 7792 | 87 | 0 | 1.51441 |
| C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase0/outputs/matrix_results/breakout_retest/cell_8_breakout_retest_dukascopy_median_trades.csv | 7792 | 87 | 0 | 1.51438 |
| C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase0/outputs/matrix_results/breakout_retest/cell_9_breakout_retest_dukascopy_p95_trades.csv | 7792 | 87 | 0 | 1.39937 |

## Review Note

Neutral intrabar ordering is intentionally not inferred from OHLC bars. If this report shows material ambiguity, the next review step is tick-level replay or a separately specified neutral ordering simulator before Phase 1 approval.

CSV summary: outputs/reports/breakout_retest_intrabar_ambiguity_summary.csv
