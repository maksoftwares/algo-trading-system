# A1 XAU M5 Momentum Continuation Variant Backtests

Generated: `2026-07-07T13:32:55.562743+00:00`
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
| `bear_quality_m5_ema_slope50` | `209` | `30.14%` | `-114.17` | `0.83` | `198.31 (18.86%)` | `-114.17` | `0` | `fail` |
| `bear_quality_m5_ema_slope100` | `134` | `28.36%` | `-113.67` | `0.75` | `184.00 (17.28%)` | `-113.67` | `0` | `fail` |
| `bear_quality_break_run_tight` | `192` | `27.6%` | `-145.26` | `0.76` | `209.70 (20.31%)` | `-145.26` | `0` | `fail` |
| `bear_quality_compression_break` | `0` | `0.0%` | `0` | `None` | `0.00 (0.00%)` | `0` | `0` | `fail` |
| `bear_quality_h4_pullback_d1bias` | `18` | `33.33%` | `51.4` | `1.34` | `92.44 (8.54%)` | `51.4` | `0` | `too_few_trades` |
| `bear_quality_weekly_rejection` | `8` | `12.5%` | `-49.91` | `0.26` | `72.96 (7.13%)` | `-49.91` | `0` | `fail` |

## Winner Status

- Status: `NO_VARIANT_CLEARS_MINIMUM_BAR`
- Note: Positive diagnostic variants still need forward confirmation before runtime promotion.

## Artifacts

### `bear_quality_m5_ema_slope50`

- Label: Bear quality: M5 EMA short, D1/H1/H4 down, stronger candle and cost filters, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_quality_first_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_QUALITY_FIRST_202207_202606_XAUUSD_M5_bear_quality_m5_ema_slope50.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_quality_first_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_QUALITY_FIRST_202207_202606_XAUUSD_M5_bear_quality_m5_ema_slope50_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_quality_first_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_QUALITY_FIRST_202207_202606_XAUUSD_M5_bear_quality_m5_ema_slope50_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_quality_first_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_QUALITY_FIRST_202207_202606_XAUUSD_M5_bear_quality_m5_ema_slope50_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_quality_first_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_QUALITY_FIRST_202207_202606_XAUUSD_M5_bear_quality_m5_ema_slope50_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_quality_first_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_QUALITY_FIRST_202207_202606_XAUUSD_M5_bear_quality_m5_ema_slope50_summary.json`
- Order activity: `{"rows": 10767, "actions": {"ORDER_SEND_OK": 209, "GUARD_BLOCK": 10558}, "guard_reasons": {"pass": 209, "own_position_exists": 271, "direction_mode_block": 5291, "blocked_entry_day_hour": 99, "h1_trend_filter_block": 3650, "h4_trend_filter_block": 668, "cooldown_active": 44, "d1_support_state_gate": 268, "estimated_cost_r_too_high": 133, "three_bar_move_atr_exceeds_cap": 3, "stop_ceiling_exceeded": 131}}`

### `bear_quality_m5_ema_slope100`

- Label: Bear quality: M5 EMA short, stronger H1/H4 slope, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_quality_first_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_QUALITY_FIRST_202207_202606_XAUUSD_M5_bear_quality_m5_ema_slope100.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_quality_first_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_QUALITY_FIRST_202207_202606_XAUUSD_M5_bear_quality_m5_ema_slope100_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_quality_first_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_QUALITY_FIRST_202207_202606_XAUUSD_M5_bear_quality_m5_ema_slope100_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_quality_first_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_QUALITY_FIRST_202207_202606_XAUUSD_M5_bear_quality_m5_ema_slope100_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_quality_first_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_QUALITY_FIRST_202207_202606_XAUUSD_M5_bear_quality_m5_ema_slope100_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_quality_first_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_QUALITY_FIRST_202207_202606_XAUUSD_M5_bear_quality_m5_ema_slope100_summary.json`
- Order activity: `{"rows": 8544, "actions": {"ORDER_SEND_OK": 134, "GUARD_BLOCK": 8410}, "guard_reasons": {"pass": 134, "own_position_exists": 138, "direction_mode_block": 4197, "blocked_entry_day_hour": 82, "h1_trend_filter_block": 3136, "h4_trend_filter_block": 450, "cooldown_active": 24, "d1_support_state_gate": 193, "estimated_cost_r_too_high": 86, "stop_ceiling_exceeded": 104}}`

### `bear_quality_break_run_tight`

- Label: Bear quality: tight break-and-run short, D1/H1/H4 down, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_quality_first_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_QUALITY_FIRST_202207_202606_XAUUSD_M5_bear_quality_break_run_tight.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_quality_first_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_QUALITY_FIRST_202207_202606_XAUUSD_M5_bear_quality_break_run_tight_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_quality_first_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_QUALITY_FIRST_202207_202606_XAUUSD_M5_bear_quality_break_run_tight_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_quality_first_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_QUALITY_FIRST_202207_202606_XAUUSD_M5_bear_quality_break_run_tight_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_quality_first_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_QUALITY_FIRST_202207_202606_XAUUSD_M5_bear_quality_break_run_tight_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_quality_first_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_QUALITY_FIRST_202207_202606_XAUUSD_M5_bear_quality_break_run_tight_summary.json`
- Order activity: `{"rows": 18105, "actions": {"ORDER_SEND_OK": 192, "GUARD_BLOCK": 17913}, "guard_reasons": {"pass": 192, "own_position_exists": 130, "three_bar_move_atr_exceeds_cap": 6739, "direction_mode_block": 4790, "h1_trend_filter_block": 2847, "break_distance_atr_exceeds_cap": 2574, "blocked_entry_day_hour": 65, "cooldown_active": 25, "h4_trend_filter_block": 413, "d1_support_state_gate": 166, "estimated_cost_r_too_high": 74, "stop_ceiling_exceeded": 90}}`

### `bear_quality_compression_break`

- Label: Bear quality: compression then downside expansion, D1/H1/H4 down, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_quality_first_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_QUALITY_FIRST_202207_202606_XAUUSD_M5_bear_quality_compression_break.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_quality_first_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_QUALITY_FIRST_202207_202606_XAUUSD_M5_bear_quality_compression_break_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_quality_first_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_QUALITY_FIRST_202207_202606_XAUUSD_M5_bear_quality_compression_break_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_quality_first_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_QUALITY_FIRST_202207_202606_XAUUSD_M5_bear_quality_compression_break_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_quality_first_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_QUALITY_FIRST_202207_202606_XAUUSD_M5_bear_quality_compression_break_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_quality_first_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_QUALITY_FIRST_202207_202606_XAUUSD_M5_bear_quality_compression_break_summary.json`
- Order activity: `{"rows": 6, "actions": {"GUARD_BLOCK": 6}, "guard_reasons": {"three_bar_move_atr_exceeds_cap": 3, "direction_mode_block": 1, "h1_trend_filter_block": 2}}`

### `bear_quality_h4_pullback_d1bias`

- Label: Bear quality: H4 pullback continuation with D1 bearish bias, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_quality_first_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_QUALITY_FIRST_202207_202606_XAUUSD_M5_bear_quality_h4_pullback_d1bias.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_quality_first_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_QUALITY_FIRST_202207_202606_XAUUSD_M5_bear_quality_h4_pullback_d1bias_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_quality_first_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_QUALITY_FIRST_202207_202606_XAUUSD_M5_bear_quality_h4_pullback_d1bias_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_quality_first_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_QUALITY_FIRST_202207_202606_XAUUSD_M5_bear_quality_h4_pullback_d1bias_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_quality_first_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_QUALITY_FIRST_202207_202606_XAUUSD_M5_bear_quality_h4_pullback_d1bias_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_quality_first_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_QUALITY_FIRST_202207_202606_XAUUSD_M5_bear_quality_h4_pullback_d1bias_summary.json`
- Order activity: `{"rows": 637, "actions": {"ORDER_SEND_OK": 18, "GUARD_BLOCK": 619}, "guard_reasons": {"pass": 18, "own_position_exists": 34, "stop_ceiling_exceeded": 9, "d1_support_state_gate": 15, "blocked_entry_day_hour": 18, "direction_mode_block": 543}}`

### `bear_quality_weekly_rejection`

- Label: Bear quality: weekly resistance rejection inside bearish D1 state, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_quality_first_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_QUALITY_FIRST_202207_202606_XAUUSD_M5_bear_quality_weekly_rejection.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_quality_first_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_QUALITY_FIRST_202207_202606_XAUUSD_M5_bear_quality_weekly_rejection_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_quality_first_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_QUALITY_FIRST_202207_202606_XAUUSD_M5_bear_quality_weekly_rejection_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_quality_first_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_QUALITY_FIRST_202207_202606_XAUUSD_M5_bear_quality_weekly_rejection_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_quality_first_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_QUALITY_FIRST_202207_202606_XAUUSD_M5_bear_quality_weekly_rejection_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_quality_first_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_QUALITY_FIRST_202207_202606_XAUUSD_M5_bear_quality_weekly_rejection_summary.json`
- Order activity: `{"rows": 238, "actions": {"GUARD_BLOCK": 230, "ORDER_SEND_OK": 8}, "guard_reasons": {"direction_mode_block": 99, "blocked_entry_day_hour": 10, "d1_support_state_gate": 116, "pass": 8, "own_position_exists": 3, "stop_ceiling_exceeded": 2}}`

## Interpretation

The baseline failed because long-side momentum entries were much worse than shorts. If a variant improves materially, it should be treated as a hypothesis for forward testing, not as a proof of profitability. The cleanest next action is to forward-observe or demo-test only the winning diagnostic variant at minimum size, with the baseline retained as the control.
