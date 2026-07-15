# A1 XAU M5 Momentum Continuation Variant Backtests

Generated: `2026-07-15T21:52:43.439112+00:00`
Period: `2016.07.01 -> 2026.06.30`
Tester currency: `USD`

## Boundary

- Offline MT5 Strategy Tester only.
- No chart, preset, order, or live/demo runtime change was made by this script.
- Variants were limited to pre-declared cells and fixed inputs; no post-result threshold sweep.
- Any positive result here is diagnostic only and requires fresh forward confirmation.
- Profit/loss table values are in tester currency `USD`.

## Variants

| Variant | Trades | Win Rate | Net USD | PF | Max Equity DD | Short USD | Long USD | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `r1_box_clean_strict_uptrend` | `367` | `53.68%` | `12014.82` | `2.94` | `1 733.37 (14.43%)` | `0` | `12014.82` | `diagnostic_only` |
| `r2_pullback_short_h1_confirm` | `689` | `36.72%` | `825.47` | `1.3` | `270.01 (23.65%)` | `825.47` | `0` | `diagnostic_only` |

## Winner Status

- Status: `DIAGNOSTIC_WINNER_NOT_PROMOTED`
- Note: This is a backtest-window diagnostic. Do not promote without fresh forward evidence.

## Artifacts

### `r1_box_clean_strict_uptrend`

- Label: Clean R1 box2 long: strict uptrend, no calendar or previous-PnL masks, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system-xau-duka-session-v1\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_a3_ml_regime_portfolio_continuous_10y_20260713_20260701\A1XauM5Momentum_A3_ML_REGIME_PORTFOLIO_CONTINUOUS_10Y_20260713_XAUUSD_M5_r1_box_clean_strict_uptrend.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system-xau-duka-session-v1\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_a3_ml_regime_portfolio_continuous_10y_20260713_20260701\A1XauM5Momentum_A3_ML_REGIME_PORTFOLIO_CONTINUOUS_10Y_20260713_XAUUSD_M5_r1_box_clean_strict_uptrend_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system-xau-duka-session-v1\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_a3_ml_regime_portfolio_continuous_10y_20260713_20260701\A1XauM5Momentum_A3_ML_REGIME_PORTFOLIO_CONTINUOUS_10Y_20260713_XAUUSD_M5_r1_box_clean_strict_uptrend_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system-xau-duka-session-v1\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_a3_ml_regime_portfolio_continuous_10y_20260713_20260701\A1XauM5Momentum_A3_ML_REGIME_PORTFOLIO_CONTINUOUS_10Y_20260713_XAUUSD_M5_r1_box_clean_strict_uptrend_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system-xau-duka-session-v1\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_a3_ml_regime_portfolio_continuous_10y_20260713_20260701\A1XauM5Momentum_A3_ML_REGIME_PORTFOLIO_CONTINUOUS_10Y_20260713_XAUUSD_M5_r1_box_clean_strict_uptrend_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system-xau-duka-session-v1\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_a3_ml_regime_portfolio_continuous_10y_20260713_20260701\A1XauM5Momentum_A3_ML_REGIME_PORTFOLIO_CONTINUOUS_10Y_20260713_XAUUSD_M5_r1_box_clean_strict_uptrend_summary.json`
- Order activity: `{"rows": 1663, "actions": {"GUARD_BLOCK": 1293, "ORDER_SEND_OK": 367, "ORDER_SEND_FAIL": 3}, "guard_reasons": {"direction_mode_block": 702, "regime_router_block_long_r1_uptrend_only_state_chop": 272, "pass": 367, "regime_router_block_long_r1_uptrend_only_state_compression": 269, "regime_router_block_long_r1_uptrend_only_state_shock": 47, "regime_router_block_long_r1_uptrend_only_state_downtrend": 3, "order_send_failed": 3}}`

### `r2_pullback_short_h1_confirm`

- Label: Strict R2 failed-rally short, H1 rejection confirmation, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system-xau-duka-session-v1\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_a3_ml_regime_portfolio_continuous_10y_20260713_20260701\A1XauM5Momentum_A3_ML_REGIME_PORTFOLIO_CONTINUOUS_10Y_20260713_XAUUSD_M5_r2_pullback_short_h1_confirm.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system-xau-duka-session-v1\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_a3_ml_regime_portfolio_continuous_10y_20260713_20260701\A1XauM5Momentum_A3_ML_REGIME_PORTFOLIO_CONTINUOUS_10Y_20260713_XAUUSD_M5_r2_pullback_short_h1_confirm_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system-xau-duka-session-v1\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_a3_ml_regime_portfolio_continuous_10y_20260713_20260701\A1XauM5Momentum_A3_ML_REGIME_PORTFOLIO_CONTINUOUS_10Y_20260713_XAUUSD_M5_r2_pullback_short_h1_confirm_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system-xau-duka-session-v1\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_a3_ml_regime_portfolio_continuous_10y_20260713_20260701\A1XauM5Momentum_A3_ML_REGIME_PORTFOLIO_CONTINUOUS_10Y_20260713_XAUUSD_M5_r2_pullback_short_h1_confirm_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system-xau-duka-session-v1\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_a3_ml_regime_portfolio_continuous_10y_20260713_20260701\A1XauM5Momentum_A3_ML_REGIME_PORTFOLIO_CONTINUOUS_10Y_20260713_XAUUSD_M5_r2_pullback_short_h1_confirm_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system-xau-duka-session-v1\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_a3_ml_regime_portfolio_continuous_10y_20260713_20260701\A1XauM5Momentum_A3_ML_REGIME_PORTFOLIO_CONTINUOUS_10Y_20260713_XAUUSD_M5_r2_pullback_short_h1_confirm_summary.json`
- Order activity: `{"rows": 3065, "actions": {"GUARD_BLOCK": 2375, "ORDER_SEND_OK": 689, "ORDER_SEND_FAIL": 1}, "guard_reasons": {"regime_router_block_short_r2_downtrend_only_state_uptrend": 43, "regime_router_block_short_r2_downtrend_only_state_chop": 1266, "regime_router_block_short_r2_downtrend_only_state_compression": 522, "regime_router_block_short_r2_downtrend_only_state_shock": 454, "pass": 689, "stop_ceiling_exceeded": 84, "max_open_positions_reached": 6, "order_send_failed": 1}}`

## Interpretation

The baseline failed because long-side momentum entries were much worse than shorts. If a variant improves materially, it should be treated as a hypothesis for forward testing, not as a proof of profitability. The cleanest next action is to forward-observe or demo-test only the winning diagnostic variant at minimum size, with the baseline retained as the control.
