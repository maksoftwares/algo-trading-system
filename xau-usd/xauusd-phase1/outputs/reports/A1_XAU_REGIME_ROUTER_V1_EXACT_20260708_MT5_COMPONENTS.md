# A1 XAU M5 Momentum Continuation Variant Backtests

Generated: `2026-07-08T13:34:33.331082+00:00`
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
| `router_v1_r1_long_box2_prevhealth` | `145` | `59.31%` | `7050.42` | `3.18` | `1 733.37 (24.59%)` | `0` | `7050.42` | `diagnostic_only` |
| `router_v1_r2_short_v4_structural` | `0` | `0.0%` | `0` | `None` | `0.00 (0.00%)` | `0` | `0` | `fail` |

## Winner Status

- Status: `DIAGNOSTIC_WINNER_NOT_PROMOTED`
- Note: This is a backtest-window diagnostic. Do not promote without fresh forward evidence.

## Artifacts

### `router_v1_r1_long_box2_prevhealth`

- Label: Router V1: H4/D1 box2 previous-month-health long armed only in R1 uptrend
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_regime_router_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_REGIME_ROUTER_V1_EXACT_202207_202606_XAUUSD_M5_router_v1_r1_long_box2_prevhealth.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_regime_router_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_REGIME_ROUTER_V1_EXACT_202207_202606_XAUUSD_M5_router_v1_r1_long_box2_prevhealth_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_regime_router_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_REGIME_ROUTER_V1_EXACT_202207_202606_XAUUSD_M5_router_v1_r1_long_box2_prevhealth_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_regime_router_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_REGIME_ROUTER_V1_EXACT_202207_202606_XAUUSD_M5_router_v1_r1_long_box2_prevhealth_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_regime_router_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_REGIME_ROUTER_V1_EXACT_202207_202606_XAUUSD_M5_router_v1_r1_long_box2_prevhealth_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_regime_router_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_REGIME_ROUTER_V1_EXACT_202207_202606_XAUUSD_M5_router_v1_r1_long_box2_prevhealth_summary.json`
- Order activity: `{"rows": 633, "actions": {"GUARD_BLOCK": 485, "ORDER_SEND_OK": 145, "ORDER_SEND_FAIL": 3}, "guard_reasons": {"direction_mode_block": 261, "regime_router_block_long_r1_uptrend_only_state_chop": 87, "regime_router_block_long_r1_uptrend_only_state_compression": 53, "blocked_entry_day_hour": 24, "regime_router_block_long_r1_uptrend_only_state_shock": 30, "pass": 145, "h4_d1_previous_month_health_gate": 29, "order_send_failed": 3, "regime_router_block_long_r1_uptrend_only_state_downtrend": 1}}`

### `router_v1_r2_short_v4_structural`

- Label: Router V1: V4 downside impulse/retest short armed only in R2 downtrend
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_regime_router_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_REGIME_ROUTER_V1_EXACT_202207_202606_XAUUSD_M5_router_v1_r2_short_v4_structural.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_regime_router_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_REGIME_ROUTER_V1_EXACT_202207_202606_XAUUSD_M5_router_v1_r2_short_v4_structural_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_regime_router_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_REGIME_ROUTER_V1_EXACT_202207_202606_XAUUSD_M5_router_v1_r2_short_v4_structural_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_regime_router_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_REGIME_ROUTER_V1_EXACT_202207_202606_XAUUSD_M5_router_v1_r2_short_v4_structural_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_regime_router_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_REGIME_ROUTER_V1_EXACT_202207_202606_XAUUSD_M5_router_v1_r2_short_v4_structural_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_regime_router_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_REGIME_ROUTER_V1_EXACT_202207_202606_XAUUSD_M5_router_v1_r2_short_v4_structural_summary.json`
- Order activity: `{"rows": 4914, "actions": {"GUARD_BLOCK": 4914}, "guard_reasons": {"h4_trend_filter_block": 457, "h1_trend_filter_block": 150, "regime_router_block_short_r2_downtrend_only_state_compression": 515, "regime_router_block_short_r2_downtrend_only_state_shock": 843, "regime_router_block_short_r2_downtrend_only_state_chop": 1851, "regime_router_block_short_r2_downtrend_only_state_uptrend": 1098}}`

## Interpretation

The baseline failed because long-side momentum entries were much worse than shorts. If a variant improves materially, it should be treated as a hypothesis for forward testing, not as a proof of profitability. The cleanest next action is to forward-observe or demo-test only the winning diagnostic variant at minimum size, with the baseline retained as the control.
