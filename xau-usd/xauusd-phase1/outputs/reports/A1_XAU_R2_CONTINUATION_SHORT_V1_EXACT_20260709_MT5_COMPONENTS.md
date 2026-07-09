# A1 XAU M5 Momentum Continuation Variant Backtests

Generated: `2026-07-08T21:47:12.186134+00:00`
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
| `r2_break_retest_body45` | `676` | `35.36%` | `629.26` | `1.29` | `234.20 (19.87%)` | `629.26` | `0` | `diagnostic_only` |
| `r2_impulse_retest_body45` | `454` | `36.34%` | `666.43` | `1.47` | `245.40 (22.82%)` | `666.43` | `0` | `diagnostic_only` |
| `r2_impulse_retest_q55` | `238` | `37.39%` | `367.6` | `1.48` | `160.41 (15.73%)` | `367.6` | `0` | `diagnostic_only` |

## Winner Status

- Status: `DIAGNOSTIC_WINNER_NOT_PROMOTED`
- Note: This is a backtest-window diagnostic. Do not promote without fresh forward evidence.

## Artifacts

### `r2_break_retest_body45`

- Label: Strict R2 M5 bear breakdown/retest, body >= 0.45, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V1_EXACT_202207_202606_XAUUSD_M5_r2_break_retest_body45.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V1_EXACT_202207_202606_XAUUSD_M5_r2_break_retest_body45_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V1_EXACT_202207_202606_XAUUSD_M5_r2_break_retest_body45_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V1_EXACT_202207_202606_XAUUSD_M5_r2_break_retest_body45_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V1_EXACT_202207_202606_XAUUSD_M5_r2_break_retest_body45_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V1_EXACT_202207_202606_XAUUSD_M5_r2_break_retest_body45_summary.json`
- Order activity: `{"rows": 5987, "actions": {"ORDER_SEND_OK": 676, "GUARD_BLOCK": 5311}, "guard_reasons": {"pass": 676, "regime_router_block_short_r2_downtrend_only_state_compression": 635, "regime_router_block_short_r2_downtrend_only_state_shock": 945, "daily_trade_cap_reached": 39, "max_open_positions_reached": 6, "regime_router_block_short_r2_downtrend_only_state_chop": 2361, "regime_router_block_short_r2_downtrend_only_state_uptrend": 1301, "stop_ceiling_exceeded": 24}}`

### `r2_impulse_retest_body45`

- Label: Strict R2 M5 downside impulse/retest, body >= 0.45, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V1_EXACT_202207_202606_XAUUSD_M5_r2_impulse_retest_body45.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V1_EXACT_202207_202606_XAUUSD_M5_r2_impulse_retest_body45_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V1_EXACT_202207_202606_XAUUSD_M5_r2_impulse_retest_body45_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V1_EXACT_202207_202606_XAUUSD_M5_r2_impulse_retest_body45_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V1_EXACT_202207_202606_XAUUSD_M5_r2_impulse_retest_body45_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V1_EXACT_202207_202606_XAUUSD_M5_r2_impulse_retest_body45_summary.json`
- Order activity: `{"rows": 3881, "actions": {"ORDER_SEND_OK": 454, "GUARD_BLOCK": 3427}, "guard_reasons": {"pass": 454, "regime_router_block_short_r2_downtrend_only_state_compression": 409, "regime_router_block_short_r2_downtrend_only_state_shock": 653, "max_open_positions_reached": 3, "daily_trade_cap_reached": 4, "regime_router_block_short_r2_downtrend_only_state_chop": 1463, "regime_router_block_short_r2_downtrend_only_state_uptrend": 875, "stop_ceiling_exceeded": 20}}`

### `r2_impulse_retest_q55`

- Label: Strict R2 M5 downside impulse/retest quality, body >= 0.55, close <= 0.25, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V1_EXACT_202207_202606_XAUUSD_M5_r2_impulse_retest_q55.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V1_EXACT_202207_202606_XAUUSD_M5_r2_impulse_retest_q55_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V1_EXACT_202207_202606_XAUUSD_M5_r2_impulse_retest_q55_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V1_EXACT_202207_202606_XAUUSD_M5_r2_impulse_retest_q55_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V1_EXACT_202207_202606_XAUUSD_M5_r2_impulse_retest_q55_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V1_EXACT_202207_202606_XAUUSD_M5_r2_impulse_retest_q55_summary.json`
- Order activity: `{"rows": 1973, "actions": {"ORDER_SEND_OK": 238, "GUARD_BLOCK": 1735}, "guard_reasons": {"pass": 238, "regime_router_block_short_r2_downtrend_only_state_chop": 724, "regime_router_block_short_r2_downtrend_only_state_compression": 208, "regime_router_block_short_r2_downtrend_only_state_shock": 326, "regime_router_block_short_r2_downtrend_only_state_uptrend": 461, "stop_ceiling_exceeded": 16}}`

## Interpretation

The baseline failed because long-side momentum entries were much worse than shorts. If a variant improves materially, it should be treated as a hypothesis for forward testing, not as a proof of profitability. The cleanest next action is to forward-observe or demo-test only the winning diagnostic variant at minimum size, with the baseline retained as the control.
