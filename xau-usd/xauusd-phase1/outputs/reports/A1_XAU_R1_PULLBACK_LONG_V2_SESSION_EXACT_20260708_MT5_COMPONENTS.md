# A1 XAU M5 Momentum Continuation Variant Backtests

Generated: `2026-07-08T16:30:30.055710+00:00`
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
| `r1_pullback_long_v2_m15_session_09_15` | `413` | `46.97%` | `1665.94` | `1.91` | `198.90 (11.46%)` | `0` | `1665.94` | `diagnostic_only` |

## Winner Status

- Status: `DIAGNOSTIC_WINNER_NOT_PROMOTED`
- Note: This is a backtest-window diagnostic. Do not promote without fresh forward evidence.

## Artifacts

### `r1_pullback_long_v2_m15_session_09_15`

- Label: R1 H1 EMA20 pullback long, M15 confirmation, server hours 09-14, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r1_pullback_long_v2_session_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R1_PULLBACK_LONG_V2_SESSION_EXACT_202207_202606_XAUUSD_M5_r1_pullback_long_v2_m15_session_09_15.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r1_pullback_long_v2_session_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R1_PULLBACK_LONG_V2_SESSION_EXACT_202207_202606_XAUUSD_M5_r1_pullback_long_v2_m15_session_09_15_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r1_pullback_long_v2_session_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R1_PULLBACK_LONG_V2_SESSION_EXACT_202207_202606_XAUUSD_M5_r1_pullback_long_v2_m15_session_09_15_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r1_pullback_long_v2_session_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R1_PULLBACK_LONG_V2_SESSION_EXACT_202207_202606_XAUUSD_M5_r1_pullback_long_v2_m15_session_09_15_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r1_pullback_long_v2_session_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R1_PULLBACK_LONG_V2_SESSION_EXACT_202207_202606_XAUUSD_M5_r1_pullback_long_v2_m15_session_09_15_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r1_pullback_long_v2_session_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R1_PULLBACK_LONG_V2_SESSION_EXACT_202207_202606_XAUUSD_M5_r1_pullback_long_v2_m15_session_09_15_summary.json`
- Order activity: `{"rows": 3318, "actions": {"GUARD_BLOCK": 2905, "ORDER_SEND_OK": 413}, "guard_reasons": {"directional_session_filter_block": 2265, "regime_router_block_long_r1_uptrend_only_state_downtrend": 7, "regime_router_block_long_r1_uptrend_only_state_chop": 254, "regime_router_block_long_r1_uptrend_only_state_compression": 110, "regime_router_block_long_r1_uptrend_only_state_shock": 234, "pass": 413, "stop_ceiling_exceeded": 33, "spread_too_high": 2}}`

## Interpretation

The baseline failed because long-side momentum entries were much worse than shorts. If a variant improves materially, it should be treated as a hypothesis for forward testing, not as a proof of profitability. The cleanest next action is to forward-observe or demo-test only the winning diagnostic variant at minimum size, with the baseline retained as the control.
