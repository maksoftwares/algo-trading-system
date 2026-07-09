# A1 XAU M5 Momentum Continuation Variant Backtests

Generated: `2026-07-08T22:03:47.560839+00:00`
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
| `r2_impulse_break20_cap25` | `88` | `36.36%` | `175.74` | `1.53` | `100.07 (9.14%)` | `175.74` | `0` | `diagnostic_only` |
| `r2_impulse_break15_30_cap20` | `150` | `36.67%` | `229.52` | `1.43` | `112.37 (10.93%)` | `229.52` | `0` | `diagnostic_only` |
| `r2_impulse_q55_break20_cap25` | `48` | `39.58%` | `109.66` | `1.6` | `100.07 (9.17%)` | `109.66` | `0` | `diagnostic_only` |

## Winner Status

- Status: `DIAGNOSTIC_WINNER_NOT_PROMOTED`
- Note: This is a backtest-window diagnostic. Do not promote without fresh forward evidence.

## Artifacts

### `r2_impulse_break20_cap25`

- Label: Strict R2 impulse/retest, break distance 2.00-4.00 ATR, 3-bar move cap 2.50, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v2_repair_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V2_REPAIR_EXACT_202207_202606_XAUUSD_M5_r2_impulse_break20_cap25.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v2_repair_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V2_REPAIR_EXACT_202207_202606_XAUUSD_M5_r2_impulse_break20_cap25_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v2_repair_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V2_REPAIR_EXACT_202207_202606_XAUUSD_M5_r2_impulse_break20_cap25_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v2_repair_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V2_REPAIR_EXACT_202207_202606_XAUUSD_M5_r2_impulse_break20_cap25_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v2_repair_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V2_REPAIR_EXACT_202207_202606_XAUUSD_M5_r2_impulse_break20_cap25_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v2_repair_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V2_REPAIR_EXACT_202207_202606_XAUUSD_M5_r2_impulse_break20_cap25_summary.json`
- Order activity: `{"rows": 3881, "actions": {"GUARD_BLOCK": 3793, "ORDER_SEND_OK": 88}, "guard_reasons": {"break_distance_atr_below_floor": 2764, "pass": 88, "three_bar_move_atr_exceeds_cap": 346, "regime_router_block_short_r2_downtrend_only_state_shock": 126, "regime_router_block_short_r2_downtrend_only_state_chop": 288, "regime_router_block_short_r2_downtrend_only_state_compression": 66, "regime_router_block_short_r2_downtrend_only_state_uptrend": 173, "break_distance_atr_exceeds_cap": 24, "stop_ceiling_exceeded": 6}}`

### `r2_impulse_break15_30_cap20`

- Label: Strict R2 impulse/retest, break distance 1.50-3.00 ATR, 3-bar move cap 2.00, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v2_repair_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V2_REPAIR_EXACT_202207_202606_XAUUSD_M5_r2_impulse_break15_30_cap20.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v2_repair_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V2_REPAIR_EXACT_202207_202606_XAUUSD_M5_r2_impulse_break15_30_cap20_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v2_repair_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V2_REPAIR_EXACT_202207_202606_XAUUSD_M5_r2_impulse_break15_30_cap20_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v2_repair_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V2_REPAIR_EXACT_202207_202606_XAUUSD_M5_r2_impulse_break15_30_cap20_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v2_repair_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V2_REPAIR_EXACT_202207_202606_XAUUSD_M5_r2_impulse_break15_30_cap20_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v2_repair_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V2_REPAIR_EXACT_202207_202606_XAUUSD_M5_r2_impulse_break15_30_cap20_summary.json`
- Order activity: `{"rows": 3881, "actions": {"GUARD_BLOCK": 3731, "ORDER_SEND_OK": 150}, "guard_reasons": {"break_distance_atr_below_floor": 1967, "pass": 150, "three_bar_move_atr_exceeds_cap": 714, "break_distance_atr_exceeds_cap": 99, "regime_router_block_short_r2_downtrend_only_state_compression": 117, "regime_router_block_short_r2_downtrend_only_state_chop": 423, "regime_router_block_short_r2_downtrend_only_state_shock": 161, "regime_router_block_short_r2_downtrend_only_state_uptrend": 245, "stop_ceiling_exceeded": 5}}`

### `r2_impulse_q55_break20_cap25`

- Label: Strict R2 impulse/retest quality, body >= 0.55, break distance 2.00-4.00 ATR, cap 2.50, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v2_repair_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V2_REPAIR_EXACT_202207_202606_XAUUSD_M5_r2_impulse_q55_break20_cap25.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v2_repair_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V2_REPAIR_EXACT_202207_202606_XAUUSD_M5_r2_impulse_q55_break20_cap25_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v2_repair_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V2_REPAIR_EXACT_202207_202606_XAUUSD_M5_r2_impulse_q55_break20_cap25_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v2_repair_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V2_REPAIR_EXACT_202207_202606_XAUUSD_M5_r2_impulse_q55_break20_cap25_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v2_repair_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V2_REPAIR_EXACT_202207_202606_XAUUSD_M5_r2_impulse_q55_break20_cap25_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v2_repair_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V2_REPAIR_EXACT_202207_202606_XAUUSD_M5_r2_impulse_q55_break20_cap25_summary.json`
- Order activity: `{"rows": 1973, "actions": {"GUARD_BLOCK": 1925, "ORDER_SEND_OK": 48}, "guard_reasons": {"break_distance_atr_below_floor": 1341, "three_bar_move_atr_exceeds_cap": 174, "pass": 48, "regime_router_block_short_r2_downtrend_only_state_chop": 166, "regime_router_block_short_r2_downtrend_only_state_compression": 38, "regime_router_block_short_r2_downtrend_only_state_shock": 74, "regime_router_block_short_r2_downtrend_only_state_uptrend": 110, "break_distance_atr_exceeds_cap": 16, "stop_ceiling_exceeded": 6}}`

## Interpretation

The baseline failed because long-side momentum entries were much worse than shorts. If a variant improves materially, it should be treated as a hypothesis for forward testing, not as a proof of profitability. The cleanest next action is to forward-observe or demo-test only the winning diagnostic variant at minimum size, with the baseline retained as the control.
