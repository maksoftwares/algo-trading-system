# A1 XAU M5 Momentum Continuation Variant Backtests

Generated: `2026-07-09T05:59:31.680220+00:00`
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
| `r2_impulse_body45_atr45` | `59` | `55.93%` | `568.41` | `2.72` | `100.07 (6.99%)` | `568.41` | `0` | `diagnostic_only` |
| `r2_impulse_body45_atr50` | `55` | `58.18%` | `565.91` | `2.86` | `100.07 (6.92%)` | `565.91` | `0` | `diagnostic_only` |
| `r2_impulse_body45_atr45_daily_loss10` | `57` | `57.89%` | `589.46` | `2.91` | `100.07 (6.93%)` | `589.46` | `0` | `diagnostic_only` |

## Winner Status

- Status: `DIAGNOSTIC_WINNER_NOT_PROMOTED`
- Note: This is a backtest-window diagnostic. Do not promote without fresh forward evidence.

## Artifacts

### `r2_impulse_body45_atr45`

- Label: Strict R2 impulse/retest body45 with M5 ATR floor 4.50, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v4_volatility_gate_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_202207_202606_XAUUSD_M5_r2_impulse_body45_atr45.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v4_volatility_gate_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_202207_202606_XAUUSD_M5_r2_impulse_body45_atr45_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v4_volatility_gate_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_202207_202606_XAUUSD_M5_r2_impulse_body45_atr45_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v4_volatility_gate_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_202207_202606_XAUUSD_M5_r2_impulse_body45_atr45_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v4_volatility_gate_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_202207_202606_XAUUSD_M5_r2_impulse_body45_atr45_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v4_volatility_gate_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_202207_202606_XAUUSD_M5_r2_impulse_body45_atr45_summary.json`
- Order activity: `{"rows": 570, "actions": {"GUARD_BLOCK": 511, "ORDER_SEND_OK": 59}, "guard_reasons": {"regime_router_block_short_r2_downtrend_only_state_shock": 183, "regime_router_block_short_r2_downtrend_only_state_chop": 232, "regime_router_block_short_r2_downtrend_only_state_uptrend": 76, "stop_ceiling_exceeded": 20, "pass": 59}}`

### `r2_impulse_body45_atr50`

- Label: Strict R2 impulse/retest body45 with M5 ATR floor 5.00, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v4_volatility_gate_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_202207_202606_XAUUSD_M5_r2_impulse_body45_atr50.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v4_volatility_gate_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_202207_202606_XAUUSD_M5_r2_impulse_body45_atr50_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v4_volatility_gate_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_202207_202606_XAUUSD_M5_r2_impulse_body45_atr50_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v4_volatility_gate_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_202207_202606_XAUUSD_M5_r2_impulse_body45_atr50_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v4_volatility_gate_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_202207_202606_XAUUSD_M5_r2_impulse_body45_atr50_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v4_volatility_gate_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_202207_202606_XAUUSD_M5_r2_impulse_body45_atr50_summary.json`
- Order activity: `{"rows": 482, "actions": {"GUARD_BLOCK": 427, "ORDER_SEND_OK": 55}, "guard_reasons": {"regime_router_block_short_r2_downtrend_only_state_shock": 154, "regime_router_block_short_r2_downtrend_only_state_chop": 196, "regime_router_block_short_r2_downtrend_only_state_uptrend": 57, "stop_ceiling_exceeded": 20, "pass": 55}}`

### `r2_impulse_body45_atr45_daily_loss10`

- Label: Strict R2 impulse/retest body45 with M5 ATR floor 4.50 and daily loss stop -$10
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v4_volatility_gate_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_202207_202606_XAUUSD_M5_r2_impulse_body45_atr45_daily_loss10.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v4_volatility_gate_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_202207_202606_XAUUSD_M5_r2_impulse_body45_atr45_daily_loss10_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v4_volatility_gate_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_202207_202606_XAUUSD_M5_r2_impulse_body45_atr45_daily_loss10_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v4_volatility_gate_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_202207_202606_XAUUSD_M5_r2_impulse_body45_atr45_daily_loss10_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v4_volatility_gate_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_202207_202606_XAUUSD_M5_r2_impulse_body45_atr45_daily_loss10_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r2_continuation_short_v4_volatility_gate_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_202207_202606_XAUUSD_M5_r2_impulse_body45_atr45_daily_loss10_summary.json`
- Order activity: `{"rows": 570, "actions": {"GUARD_BLOCK": 513, "ORDER_SEND_OK": 57}, "guard_reasons": {"regime_router_block_short_r2_downtrend_only_state_shock": 183, "regime_router_block_short_r2_downtrend_only_state_chop": 232, "regime_router_block_short_r2_downtrend_only_state_uptrend": 76, "stop_ceiling_exceeded": 20, "pass": 57, "portfolio_daily_loss_stop_reached": 2}}`

## Interpretation

The baseline failed because long-side momentum entries were much worse than shorts. If a variant improves materially, it should be treated as a hypothesis for forward testing, not as a proof of profitability. The cleanest next action is to forward-observe or demo-test only the winning diagnostic variant at minimum size, with the baseline retained as the control.
