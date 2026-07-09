# A1 XAU M5 Momentum Continuation Variant Backtests

Generated: `2026-07-09T10:43:02.726629+00:00`
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
| `r1_long_expansion_r3_reclass_strict_r1` | `139` | `67.63%` | `10142.72` | `4.24` | `1 720.10 (15.27%)` | `0` | `10142.72` | `diagnostic_only` |

## Winner Status

- Status: `DIAGNOSTIC_WINNER_NOT_PROMOTED`
- Note: This is a backtest-window diagnostic. Do not promote without fresh forward evidence.

## Artifacts

### `r1_long_expansion_r3_reclass_strict_r1`

- Label: Strict R1-routed reclass of frozen R3 D1-compression/H4-expansion long source
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r1_long_expansion_r3_reclass_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R1_LONG_EXPANSION_R3_RECLASS_EXACT_202207_202606_XAUUSD_M5_r1_long_expansion_r3_reclass_strict_r1.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r1_long_expansion_r3_reclass_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R1_LONG_EXPANSION_R3_RECLASS_EXACT_202207_202606_XAUUSD_M5_r1_long_expansion_r3_reclass_strict_r1_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r1_long_expansion_r3_reclass_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R1_LONG_EXPANSION_R3_RECLASS_EXACT_202207_202606_XAUUSD_M5_r1_long_expansion_r3_reclass_strict_r1_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r1_long_expansion_r3_reclass_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R1_LONG_EXPANSION_R3_RECLASS_EXACT_202207_202606_XAUUSD_M5_r1_long_expansion_r3_reclass_strict_r1_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r1_long_expansion_r3_reclass_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R1_LONG_EXPANSION_R3_RECLASS_EXACT_202207_202606_XAUUSD_M5_r1_long_expansion_r3_reclass_strict_r1_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r1_long_expansion_r3_reclass_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R1_LONG_EXPANSION_R3_RECLASS_EXACT_202207_202606_XAUUSD_M5_r1_long_expansion_r3_reclass_strict_r1_summary.json`
- Order activity: `{"rows": 359, "actions": {"GUARD_BLOCK": 218, "ORDER_SEND_OK": 139, "ORDER_SEND_FAIL": 2}, "guard_reasons": {"direction_mode_block": 142, "regime_router_block_long_r1_uptrend_only_state_chop": 23, "regime_router_block_long_r1_uptrend_only_state_compression": 45, "pass": 139, "regime_router_block_long_r1_uptrend_only_state_shock": 8, "order_send_failed": 2}}`

## Interpretation

The baseline failed because long-side momentum entries were much worse than shorts. If a variant improves materially, it should be treated as a hypothesis for forward testing, not as a proof of profitability. The cleanest next action is to forward-observe or demo-test only the winning diagnostic variant at minimum size, with the baseline retained as the control.
