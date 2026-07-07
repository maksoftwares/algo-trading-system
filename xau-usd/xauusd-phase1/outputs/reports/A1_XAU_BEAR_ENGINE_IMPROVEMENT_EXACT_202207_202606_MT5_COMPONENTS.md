# A1 XAU M5 Momentum Continuation Variant Backtests

Generated: `2026-07-07T13:12:37.187182+00:00`
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
| `bear_m5_ema_h1_only_rr2_morefreq` | `438` | `33.11%` | `139.24` | `1.07` | `277.92 (25.13%)` | `139.24` | `0` | `diagnostic_only` |
| `bear_m5_ema_h1h4_rr2_strict_body` | `432` | `31.71%` | `-32.25` | `0.98` | `291.77 (26.75%)` | `-32.25` | `0` | `fail` |
| `bear_m5_ema_h1h4_rr2_fast_slope` | `406` | `33.0%` | `98.8` | `1.05` | `244.56 (22.24%)` | `98.8` | `0` | `diagnostic_only` |
| `bear_ema_pullback_h1h4_rr2` | `487` | `31.42%` | `-186.96` | `0.92` | `509.50 (47.04%)` | `-186.96` | `0` | `fail` |
| `bear_break_run_h1h4_rr2` | `445` | `32.13%` | `208.0` | `1.11` | `331.21 (30.32%)` | `208.0` | `0` | `diagnostic_only` |

## Winner Status

- Status: `DIAGNOSTIC_WINNER_NOT_PROMOTED`
- Note: This is a backtest-window diagnostic. Do not promote without fresh forward evidence.

## Artifacts

### `bear_m5_ema_h1_only_rr2_morefreq`

- Label: Bear improvement: M5 EMA short, bearish D1 + H1 only, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_engine_improvement_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_ENGINE_IMPROVEMENT_202207_202606_XAUUSD_M5_bear_m5_ema_h1_only_rr2_morefreq.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_engine_improvement_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_ENGINE_IMPROVEMENT_202207_202606_XAUUSD_M5_bear_m5_ema_h1_only_rr2_morefreq_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_engine_improvement_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_ENGINE_IMPROVEMENT_202207_202606_XAUUSD_M5_bear_m5_ema_h1_only_rr2_morefreq_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_engine_improvement_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_ENGINE_IMPROVEMENT_202207_202606_XAUUSD_M5_bear_m5_ema_h1_only_rr2_morefreq_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_engine_improvement_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_ENGINE_IMPROVEMENT_202207_202606_XAUUSD_M5_bear_m5_ema_h1_only_rr2_morefreq_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_engine_improvement_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_ENGINE_IMPROVEMENT_202207_202606_XAUUSD_M5_bear_m5_ema_h1_only_rr2_morefreq_summary.json`
- Order activity: `{"rows": 37103, "actions": {"GUARD_BLOCK": 36665, "ORDER_SEND_OK": 438}, "guard_reasons": {"direction_mode_block": 17438, "pass": 438, "own_position_exists": 2268, "h1_trend_filter_block": 12705, "blocked_entry_day_hour": 316, "d1_support_state_gate": 3378, "estimated_cost_r_too_high": 324, "stop_ceiling_exceeded": 236}}`

### `bear_m5_ema_h1h4_rr2_strict_body`

- Label: Bear improvement: M5 EMA short, strict candle quality, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_engine_improvement_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_ENGINE_IMPROVEMENT_202207_202606_XAUUSD_M5_bear_m5_ema_h1h4_rr2_strict_body.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_engine_improvement_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_ENGINE_IMPROVEMENT_202207_202606_XAUUSD_M5_bear_m5_ema_h1h4_rr2_strict_body_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_engine_improvement_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_ENGINE_IMPROVEMENT_202207_202606_XAUUSD_M5_bear_m5_ema_h1h4_rr2_strict_body_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_engine_improvement_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_ENGINE_IMPROVEMENT_202207_202606_XAUUSD_M5_bear_m5_ema_h1h4_rr2_strict_body_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_engine_improvement_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_ENGINE_IMPROVEMENT_202207_202606_XAUUSD_M5_bear_m5_ema_h1h4_rr2_strict_body_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_engine_improvement_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_ENGINE_IMPROVEMENT_202207_202606_XAUUSD_M5_bear_m5_ema_h1h4_rr2_strict_body_summary.json`
- Order activity: `{"rows": 26487, "actions": {"ORDER_SEND_OK": 432, "GUARD_BLOCK": 26055}, "guard_reasons": {"pass": 432, "own_position_exists": 1369, "direction_mode_block": 13176, "h1_trend_filter_block": 8584, "blocked_entry_day_hour": 221, "h4_trend_filter_block": 1632, "d1_support_state_gate": 715, "estimated_cost_r_too_high": 207, "stop_ceiling_exceeded": 151}}`

### `bear_m5_ema_h1h4_rr2_fast_slope`

- Label: Bear improvement: M5 EMA short, faster bearish slope, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_engine_improvement_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_ENGINE_IMPROVEMENT_202207_202606_XAUUSD_M5_bear_m5_ema_h1h4_rr2_fast_slope.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_engine_improvement_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_ENGINE_IMPROVEMENT_202207_202606_XAUUSD_M5_bear_m5_ema_h1h4_rr2_fast_slope_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_engine_improvement_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_ENGINE_IMPROVEMENT_202207_202606_XAUUSD_M5_bear_m5_ema_h1h4_rr2_fast_slope_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_engine_improvement_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_ENGINE_IMPROVEMENT_202207_202606_XAUUSD_M5_bear_m5_ema_h1h4_rr2_fast_slope_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_engine_improvement_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_ENGINE_IMPROVEMENT_202207_202606_XAUUSD_M5_bear_m5_ema_h1h4_rr2_fast_slope_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_engine_improvement_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_ENGINE_IMPROVEMENT_202207_202606_XAUUSD_M5_bear_m5_ema_h1h4_rr2_fast_slope_summary.json`
- Order activity: `{"rows": 26879, "actions": {"GUARD_BLOCK": 26473, "ORDER_SEND_OK": 406}, "guard_reasons": {"direction_mode_block": 12546, "pass": 406, "own_position_exists": 1549, "h1_trend_filter_block": 9166, "blocked_entry_day_hour": 241, "h4_trend_filter_block": 1779, "d1_support_state_gate": 785, "estimated_cost_r_too_high": 237, "stop_ceiling_exceeded": 170}}`

### `bear_ema_pullback_h1h4_rr2`

- Label: Bear improvement: EMA pullback short, bearish D1 + H1/H4, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_engine_improvement_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_ENGINE_IMPROVEMENT_202207_202606_XAUUSD_M5_bear_ema_pullback_h1h4_rr2.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_engine_improvement_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_ENGINE_IMPROVEMENT_202207_202606_XAUUSD_M5_bear_ema_pullback_h1h4_rr2_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_engine_improvement_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_ENGINE_IMPROVEMENT_202207_202606_XAUUSD_M5_bear_ema_pullback_h1h4_rr2_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_engine_improvement_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_ENGINE_IMPROVEMENT_202207_202606_XAUUSD_M5_bear_ema_pullback_h1h4_rr2_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_engine_improvement_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_ENGINE_IMPROVEMENT_202207_202606_XAUUSD_M5_bear_ema_pullback_h1h4_rr2_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_engine_improvement_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_ENGINE_IMPROVEMENT_202207_202606_XAUUSD_M5_bear_ema_pullback_h1h4_rr2_summary.json`
- Order activity: `{"rows": 44424, "actions": {"GUARD_BLOCK": 43935, "ORDER_SEND_OK": 487, "ORDER_SEND_FAIL": 2}, "guard_reasons": {"direction_mode_block": 20603, "pass": 487, "own_position_exists": 2078, "h1_trend_filter_block": 16841, "blocked_entry_day_hour": 359, "estimated_cost_r_too_high": 352, "h4_trend_filter_block": 2515, "d1_support_state_gate": 989, "order_send_failed": 2, "stop_ceiling_exceeded": 198}}`

### `bear_break_run_h1h4_rr2`

- Label: Bear improvement: break-and-run short, bearish D1 + H1/H4, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_engine_improvement_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_ENGINE_IMPROVEMENT_202207_202606_XAUUSD_M5_bear_break_run_h1h4_rr2.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_engine_improvement_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_ENGINE_IMPROVEMENT_202207_202606_XAUUSD_M5_bear_break_run_h1h4_rr2_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_engine_improvement_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_ENGINE_IMPROVEMENT_202207_202606_XAUUSD_M5_bear_break_run_h1h4_rr2_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_engine_improvement_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_ENGINE_IMPROVEMENT_202207_202606_XAUUSD_M5_bear_break_run_h1h4_rr2_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_engine_improvement_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_ENGINE_IMPROVEMENT_202207_202606_XAUUSD_M5_bear_break_run_h1h4_rr2_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_bear_engine_improvement_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_BEAR_ENGINE_IMPROVEMENT_202207_202606_XAUUSD_M5_bear_break_run_h1h4_rr2_summary.json`
- Order activity: `{"rows": 24379, "actions": {"ORDER_SEND_OK": 445, "GUARD_BLOCK": 23934}, "guard_reasons": {"pass": 445, "own_position_exists": 1019, "direction_mode_block": 12258, "h1_trend_filter_block": 8268, "blocked_entry_day_hour": 163, "h4_trend_filter_block": 1355, "d1_support_state_gate": 576, "estimated_cost_r_too_high": 160, "stop_ceiling_exceeded": 135}}`

## Interpretation

The baseline failed because long-side momentum entries were much worse than shorts. If a variant improves materially, it should be treated as a hypothesis for forward testing, not as a proof of profitability. The cleanest next action is to forward-observe or demo-test only the winning diagnostic variant at minimum size, with the baseline retained as the control.
