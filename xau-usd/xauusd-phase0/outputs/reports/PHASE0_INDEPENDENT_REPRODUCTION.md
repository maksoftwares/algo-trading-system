# Phase 0 Independent Reproduction

Overall status: PASS

## Scope

| Field | Value |
| --- | --- |
| expert | breakout_retest |
| cell_id | 2 |
| broker | capital_com |
| cost_model | median |
| symbol | XAUUSD |
| method | standalone_pandas_event_replay |
| tolerance_pct | 5.00 |

## Source Artifacts

| Artifact | Path |
| --- | --- |
| M5 bars | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase0\data\processed\bars\capital_com\XAUUSD\M5\XAUUSD_capital_com_M5_20160103_20250701.csv |
| Reference matrix summary | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase0\outputs\matrix_results\breakout_retest\cell_2_breakout_retest_capital_com_median.csv |
| Reference trade ledger | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase0\outputs\matrix_results\breakout_retest\cell_2_breakout_retest_capital_com_median_trades.csv |

## Comparison

| Metric | Reference | Independent | Delta % | Tolerance % | Status |
| --- | --- | --- | --- | --- | --- |
| trade_count | 7287.00 | 7287.00 | 0 | 5 | PASS |
| profit_factor | 1.41196 | 1.41196 | 0 | 5 | PASS |
| win_rate | 0.484424 | 0.484424 | 0 | 5 | PASS |
| total_pnl_usd | 18642279.99 | 18642279.99 | 0 | 5 | PASS |
| max_drawdown_pct | 9.81275 | 9.81275 | 1.81025e-13 | 5 | PASS |

## Independent Metrics

| Metric | Value |
| --- | --- |
| trade_count | 7287.00 |
| profit_factor | 1.41196 |
| win_rate | 0.484424 |
| total_pnl_usd | 18642279.99 |
| total_return_pct | 186422.80 |
| max_drawdown_pct | 9.81275 |
| avg_trade_R | 0.210694 |
| median_trade_R | -0.990053 |

## Notes

- Independent trade rows simulated: 7287
- This replay does not call the Phase 0 strategy class, execution simulator, or metrics module.
- It uses the same processed M5 bars and the same pre-registered mechanical rules for the selected approved cell.
- This closes D4 for the selected cell if every comparison row is PASS.
