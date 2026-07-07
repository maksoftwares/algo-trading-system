# A1 XAU M5 Momentum Continuation Variant Backtests

Generated: `2026-07-07T12:37:51.481050+00:00`
Period: `2022.07.01 -> 2026.06.30`
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
| `down_h4_d1_short_box2_atr80` | `103` | `27.18%` | `-993.77` | `0.63` | `2 451.10 (99.76%)` | `-993.77` | `0` | `fail` |
| `down_h1_d1_short_box2_atr80` | `181` | `29.28%` | `-986.04` | `0.76` | `3 974.12 (100.35%)` | `-986.04` | `0` | `fail` |
| `down_m5_ema_h1h4_short_rr2` | `438` | `33.11%` | `137.34` | `1.07` | `246.63 (22.46%)` | `137.34` | `0` | `diagnostic_only` |
| `down_prior_day_cont_short_rr2` | `354` | `30.23%` | `-175.48` | `0.86` | `402.50 (39.43%)` | `-175.48` | `0` | `fail` |

## Winner Status

- Status: `NO_VARIANT_CLEARS_MINIMUM_BAR`
- Note: Positive diagnostic variants still need forward confirmation before runtime promotion.

## Artifacts

### `down_h4_d1_short_box2_atr80`

- Label: Bearish-D1 H4/D1 compression expansion, short-only, box2 ATR80, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_downtrend_short_engine_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_DOWNTREND_SHORT_ENGINE_202207_202606_XAUUSD_M5_down_h4_d1_short_box2_atr80.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_downtrend_short_engine_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_DOWNTREND_SHORT_ENGINE_202207_202606_XAUUSD_M5_down_h4_d1_short_box2_atr80_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_downtrend_short_engine_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_DOWNTREND_SHORT_ENGINE_202207_202606_XAUUSD_M5_down_h4_d1_short_box2_atr80_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_downtrend_short_engine_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_DOWNTREND_SHORT_ENGINE_202207_202606_XAUUSD_M5_down_h4_d1_short_box2_atr80_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_downtrend_short_engine_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_DOWNTREND_SHORT_ENGINE_202207_202606_XAUUSD_M5_down_h4_d1_short_box2_atr80_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_downtrend_short_engine_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_DOWNTREND_SHORT_ENGINE_202207_202606_XAUUSD_M5_down_h4_d1_short_box2_atr80_summary.json`
- Order activity: `{"rows": 504, "actions": {"ORDER_SEND_OK": 103, "GUARD_BLOCK": 400, "ORDER_SEND_FAIL": 1}, "guard_reasons": {"pass": 103, "direction_mode_block": 264, "d1_support_state_gate": 116, "blocked_entry_day_hour": 20, "order_send_failed": 1}}`

### `down_h1_d1_short_box2_atr80`

- Label: Bearish-D1 H1/D1 compression expansion, short-only, box2 ATR80, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_downtrend_short_engine_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_DOWNTREND_SHORT_ENGINE_202207_202606_XAUUSD_M5_down_h1_d1_short_box2_atr80.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_downtrend_short_engine_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_DOWNTREND_SHORT_ENGINE_202207_202606_XAUUSD_M5_down_h1_d1_short_box2_atr80_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_downtrend_short_engine_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_DOWNTREND_SHORT_ENGINE_202207_202606_XAUUSD_M5_down_h1_d1_short_box2_atr80_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_downtrend_short_engine_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_DOWNTREND_SHORT_ENGINE_202207_202606_XAUUSD_M5_down_h1_d1_short_box2_atr80_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_downtrend_short_engine_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_DOWNTREND_SHORT_ENGINE_202207_202606_XAUUSD_M5_down_h1_d1_short_box2_atr80_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_downtrend_short_engine_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_DOWNTREND_SHORT_ENGINE_202207_202606_XAUUSD_M5_down_h1_d1_short_box2_atr80_summary.json`
- Order activity: `{"rows": 587, "actions": {"ORDER_SEND_OK": 181, "GUARD_BLOCK": 405, "ORDER_SEND_FAIL": 1}, "guard_reasons": {"pass": 181, "direction_mode_block": 280, "daily_trade_cap_reached": 11, "d1_support_state_gate": 102, "max_open_positions_reached": 6, "blocked_entry_day_hour": 6, "order_send_failed": 1}}`

### `down_m5_ema_h1h4_short_rr2`

- Label: Bearish-D1 M5 EMA trend continuation, H1/H4 aligned, short-only, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_downtrend_short_engine_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_DOWNTREND_SHORT_ENGINE_202207_202606_XAUUSD_M5_down_m5_ema_h1h4_short_rr2.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_downtrend_short_engine_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_DOWNTREND_SHORT_ENGINE_202207_202606_XAUUSD_M5_down_m5_ema_h1h4_short_rr2_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_downtrend_short_engine_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_DOWNTREND_SHORT_ENGINE_202207_202606_XAUUSD_M5_down_m5_ema_h1h4_short_rr2_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_downtrend_short_engine_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_DOWNTREND_SHORT_ENGINE_202207_202606_XAUUSD_M5_down_m5_ema_h1h4_short_rr2_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_downtrend_short_engine_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_DOWNTREND_SHORT_ENGINE_202207_202606_XAUUSD_M5_down_m5_ema_h1h4_short_rr2_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_downtrend_short_engine_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_DOWNTREND_SHORT_ENGINE_202207_202606_XAUUSD_M5_down_m5_ema_h1h4_short_rr2_summary.json`
- Order activity: `{"rows": 37103, "actions": {"GUARD_BLOCK": 36665, "ORDER_SEND_OK": 438}, "guard_reasons": {"direction_mode_block": 17438, "pass": 438, "own_position_exists": 2192, "h1_trend_filter_block": 12705, "blocked_entry_day_hour": 316, "h4_trend_filter_block": 2403, "d1_support_state_gate": 1068, "estimated_cost_r_too_high": 317, "stop_ceiling_exceeded": 226}}`

### `down_prior_day_cont_short_rr2`

- Label: Bearish-D1 prior-day level continuation, short-only, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_downtrend_short_engine_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_DOWNTREND_SHORT_ENGINE_202207_202606_XAUUSD_M5_down_prior_day_cont_short_rr2.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_downtrend_short_engine_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_DOWNTREND_SHORT_ENGINE_202207_202606_XAUUSD_M5_down_prior_day_cont_short_rr2_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_downtrend_short_engine_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_DOWNTREND_SHORT_ENGINE_202207_202606_XAUUSD_M5_down_prior_day_cont_short_rr2_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_downtrend_short_engine_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_DOWNTREND_SHORT_ENGINE_202207_202606_XAUUSD_M5_down_prior_day_cont_short_rr2_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_downtrend_short_engine_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_DOWNTREND_SHORT_ENGINE_202207_202606_XAUUSD_M5_down_prior_day_cont_short_rr2_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_downtrend_short_engine_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_DOWNTREND_SHORT_ENGINE_202207_202606_XAUUSD_M5_down_prior_day_cont_short_rr2_summary.json`
- Order activity: `{"rows": 21930, "actions": {"ORDER_SEND_OK": 354, "GUARD_BLOCK": 21576}, "guard_reasons": {"pass": 354, "cooldown_active": 133, "own_position_exists": 1970, "stop_ceiling_exceeded": 1075, "direction_mode_block": 12657, "blocked_entry_day_hour": 285, "d1_support_state_gate": 5427, "estimated_cost_r_too_high": 29}}`

## Interpretation

The baseline failed because long-side momentum entries were much worse than shorts. If a variant improves materially, it should be treated as a hypothesis for forward testing, not as a proof of profitability. The cleanest next action is to forward-observe or demo-test only the winning diagnostic variant at minimum size, with the baseline retained as the control.
