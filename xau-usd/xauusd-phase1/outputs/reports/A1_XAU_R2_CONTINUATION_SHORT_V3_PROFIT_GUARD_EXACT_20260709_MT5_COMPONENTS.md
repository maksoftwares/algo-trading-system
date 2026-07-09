# A1 XAU M5 Momentum Continuation Variant Backtests

Generated: `2026-07-08T22:17:34.356788+00:00`
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
| `r2_impulse_body45_daily_loss7` | `340` | `34.41%` | `505.41` | `1.44` | `317.89 (31.08%)` | `505.41` | `0` | `diagnostic_only` |
| `r2_impulse_body45_daily_loss10` | `387` | `34.63%` | `575.54` | `1.46` | `251.68 (23.49%)` | `575.54` | `0` | `diagnostic_only` |
| `r2_impulse_body45_loss_cooldown240` | `372` | `36.56%` | `660.83` | `1.55` | `282.48 (26.58%)` | `660.83` | `0` | `diagnostic_only` |

## Winner Status

- Status: `DIAGNOSTIC_WINNER_NOT_PROMOTED`
- Note: This is a backtest-window diagnostic. Do not promote without fresh forward evidence.

## Artifacts

### `r2_impulse_body45_daily_loss7`

- Label: Strict R2 impulse/retest body45 with portfolio daily loss stop -$7
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v3_profit_guard_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_EXACT_202207_202606_XAUUSD_M5_r2_impulse_body45_daily_loss7.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v3_profit_guard_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_EXACT_202207_202606_XAUUSD_M5_r2_impulse_body45_daily_loss7_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v3_profit_guard_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_EXACT_202207_202606_XAUUSD_M5_r2_impulse_body45_daily_loss7_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v3_profit_guard_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_EXACT_202207_202606_XAUUSD_M5_r2_impulse_body45_daily_loss7_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v3_profit_guard_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_EXACT_202207_202606_XAUUSD_M5_r2_impulse_body45_daily_loss7_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v3_profit_guard_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_EXACT_202207_202606_XAUUSD_M5_r2_impulse_body45_daily_loss7_summary.json`
- Order activity: `{"rows": 3881, "actions": {"ORDER_SEND_OK": 340, "GUARD_BLOCK": 3541}, "guard_reasons": {"pass": 340, "portfolio_daily_loss_stop_reached": 117, "regime_router_block_short_r2_downtrend_only_state_compression": 409, "regime_router_block_short_r2_downtrend_only_state_shock": 653, "regime_router_block_short_r2_downtrend_only_state_chop": 1463, "regime_router_block_short_r2_downtrend_only_state_uptrend": 875, "max_open_positions_reached": 2, "stop_ceiling_exceeded": 20, "daily_trade_cap_reached": 2}}`

### `r2_impulse_body45_daily_loss10`

- Label: Strict R2 impulse/retest body45 with portfolio daily loss stop -$10
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v3_profit_guard_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_EXACT_202207_202606_XAUUSD_M5_r2_impulse_body45_daily_loss10.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v3_profit_guard_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_EXACT_202207_202606_XAUUSD_M5_r2_impulse_body45_daily_loss10_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v3_profit_guard_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_EXACT_202207_202606_XAUUSD_M5_r2_impulse_body45_daily_loss10_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v3_profit_guard_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_EXACT_202207_202606_XAUUSD_M5_r2_impulse_body45_daily_loss10_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v3_profit_guard_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_EXACT_202207_202606_XAUUSD_M5_r2_impulse_body45_daily_loss10_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v3_profit_guard_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_EXACT_202207_202606_XAUUSD_M5_r2_impulse_body45_daily_loss10_summary.json`
- Order activity: `{"rows": 3881, "actions": {"ORDER_SEND_OK": 387, "GUARD_BLOCK": 3494}, "guard_reasons": {"pass": 387, "portfolio_daily_loss_stop_reached": 67, "regime_router_block_short_r2_downtrend_only_state_compression": 409, "regime_router_block_short_r2_downtrend_only_state_shock": 653, "max_open_positions_reached": 3, "daily_trade_cap_reached": 4, "regime_router_block_short_r2_downtrend_only_state_chop": 1463, "regime_router_block_short_r2_downtrend_only_state_uptrend": 875, "stop_ceiling_exceeded": 20}}`

### `r2_impulse_body45_loss_cooldown240`

- Label: Strict R2 impulse/retest body45 with 240 minute cooldown after closed loss
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v3_profit_guard_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_EXACT_202207_202606_XAUUSD_M5_r2_impulse_body45_loss_cooldown240.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v3_profit_guard_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_EXACT_202207_202606_XAUUSD_M5_r2_impulse_body45_loss_cooldown240_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v3_profit_guard_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_EXACT_202207_202606_XAUUSD_M5_r2_impulse_body45_loss_cooldown240_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v3_profit_guard_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_EXACT_202207_202606_XAUUSD_M5_r2_impulse_body45_loss_cooldown240_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v3_profit_guard_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_EXACT_202207_202606_XAUUSD_M5_r2_impulse_body45_loss_cooldown240_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v3_profit_guard_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_EXACT_202207_202606_XAUUSD_M5_r2_impulse_body45_loss_cooldown240_summary.json`
- Order activity: `{"rows": 3881, "actions": {"ORDER_SEND_OK": 372, "GUARD_BLOCK": 3509}, "guard_reasons": {"pass": 372, "portfolio_cooldown_after_loss_active": 87, "regime_router_block_short_r2_downtrend_only_state_compression": 409, "regime_router_block_short_r2_downtrend_only_state_shock": 653, "regime_router_block_short_r2_downtrend_only_state_chop": 1463, "regime_router_block_short_r2_downtrend_only_state_uptrend": 875, "stop_ceiling_exceeded": 20, "daily_trade_cap_reached": 2}}`

## Interpretation

The baseline failed because long-side momentum entries were much worse than shorts. If a variant improves materially, it should be treated as a hypothesis for forward testing, not as a proof of profitability. The cleanest next action is to forward-observe or demo-test only the winning diagnostic variant at minimum size, with the baseline retained as the control.
