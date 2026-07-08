# A1 XAU M5 Momentum Continuation Variant Backtests

Generated: `2026-07-08T20:32:20.903192+00:00`
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
| `r2_pullback_short_m15_confirm` | `464` | `34.91%` | `412.09` | `1.2` | `470.25 (39.10%)` | `412.09` | `0` | `diagnostic_only` |
| `r2_pullback_short_h1_confirm` | `211` | `39.34%` | `426.88` | `1.46` | `160.62 (11.13%)` | `426.88` | `0` | `diagnostic_only` |

## Winner Status

- Status: `DIAGNOSTIC_WINNER_NOT_PROMOTED`
- Note: This is a backtest-window diagnostic. Do not promote without fresh forward evidence.

## Artifacts

### `r2_pullback_short_m15_confirm`

- Label: Strict R2 failed-rally short, M15 rejection confirmation, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_pullback_rejection_short_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_PULLBACK_REJECTION_SHORT_V1_EXACT_202207_202606_XAUUSD_M5_r2_pullback_short_m15_confirm.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_pullback_rejection_short_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_PULLBACK_REJECTION_SHORT_V1_EXACT_202207_202606_XAUUSD_M5_r2_pullback_short_m15_confirm_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_pullback_rejection_short_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_PULLBACK_REJECTION_SHORT_V1_EXACT_202207_202606_XAUUSD_M5_r2_pullback_short_m15_confirm_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_pullback_rejection_short_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_PULLBACK_REJECTION_SHORT_V1_EXACT_202207_202606_XAUUSD_M5_r2_pullback_short_m15_confirm_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_pullback_rejection_short_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_PULLBACK_REJECTION_SHORT_V1_EXACT_202207_202606_XAUUSD_M5_r2_pullback_short_m15_confirm_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_pullback_rejection_short_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_PULLBACK_REJECTION_SHORT_V1_EXACT_202207_202606_XAUUSD_M5_r2_pullback_short_m15_confirm_summary.json`
- Order activity: `{"rows": 2389, "actions": {"ORDER_SEND_OK": 464, "GUARD_BLOCK": 1925}, "guard_reasons": {"pass": 464, "regime_router_block_short_r2_downtrend_only_state_shock": 297, "stop_ceiling_exceeded": 62, "daily_trade_cap_reached": 8, "regime_router_block_short_r2_downtrend_only_state_chop": 1286, "regime_router_block_short_r2_downtrend_only_state_compression": 211, "max_open_positions_reached": 31, "regime_router_block_short_r2_downtrend_only_state_uptrend": 30}}`

### `r2_pullback_short_h1_confirm`

- Label: Strict R2 failed-rally short, H1 rejection confirmation, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_pullback_rejection_short_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_PULLBACK_REJECTION_SHORT_V1_EXACT_202207_202606_XAUUSD_M5_r2_pullback_short_h1_confirm.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_pullback_rejection_short_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_PULLBACK_REJECTION_SHORT_V1_EXACT_202207_202606_XAUUSD_M5_r2_pullback_short_h1_confirm_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_pullback_rejection_short_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_PULLBACK_REJECTION_SHORT_V1_EXACT_202207_202606_XAUUSD_M5_r2_pullback_short_h1_confirm_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_pullback_rejection_short_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_PULLBACK_REJECTION_SHORT_V1_EXACT_202207_202606_XAUUSD_M5_r2_pullback_short_h1_confirm_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_pullback_rejection_short_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_PULLBACK_REJECTION_SHORT_V1_EXACT_202207_202606_XAUUSD_M5_r2_pullback_short_h1_confirm_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_pullback_rejection_short_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_PULLBACK_REJECTION_SHORT_V1_EXACT_202207_202606_XAUUSD_M5_r2_pullback_short_h1_confirm_summary.json`
- Order activity: `{"rows": 1179, "actions": {"ORDER_SEND_OK": 211, "GUARD_BLOCK": 967, "ORDER_SEND_FAIL": 1}, "guard_reasons": {"pass": 211, "regime_router_block_short_r2_downtrend_only_state_shock": 172, "stop_ceiling_exceeded": 72, "regime_router_block_short_r2_downtrend_only_state_chop": 606, "regime_router_block_short_r2_downtrend_only_state_compression": 101, "order_send_failed": 1, "regime_router_block_short_r2_downtrend_only_state_uptrend": 14, "max_open_positions_reached": 2}}`

## Interpretation

The baseline failed because long-side momentum entries were much worse than shorts. If a variant improves materially, it should be treated as a hypothesis for forward testing, not as a proof of profitability. The cleanest next action is to forward-observe or demo-test only the winning diagnostic variant at minimum size, with the baseline retained as the control.
