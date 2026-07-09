# A1 XAU M5 Momentum Continuation Variant Backtests

Generated: `2026-07-09T06:55:50.565334+00:00`
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
| `r3_compression_long_v1_broad_box3_atr60_range125_body035` | `215` | `61.4%` | `12194.08` | `3.68` | `1 720.10 (12.72%)` | `0` | `12194.08` | `diagnostic_only` |

## Winner Status

- Status: `DIAGNOSTIC_WINNER_NOT_PROMOTED`
- Note: This is a backtest-window diagnostic. Do not promote without fresh forward evidence.

## Artifacts

### `r3_compression_long_v1_broad_box3_atr60_range125_body035`

- Label: R3 D1-compression/H4-expansion long-only, broad box3 atr60 range125 body035, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r3_compression_long_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R3_COMPRESSION_LONG_V1_EXACT_202207_202606_XAUUSD_M5_r3_compression_long_v1_broad_box3_atr60_range125_body035.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r3_compression_long_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R3_COMPRESSION_LONG_V1_EXACT_202207_202606_XAUUSD_M5_r3_compression_long_v1_broad_box3_atr60_range125_body035_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r3_compression_long_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R3_COMPRESSION_LONG_V1_EXACT_202207_202606_XAUUSD_M5_r3_compression_long_v1_broad_box3_atr60_range125_body035_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r3_compression_long_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R3_COMPRESSION_LONG_V1_EXACT_202207_202606_XAUUSD_M5_r3_compression_long_v1_broad_box3_atr60_range125_body035_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r3_compression_long_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R3_COMPRESSION_LONG_V1_EXACT_202207_202606_XAUUSD_M5_r3_compression_long_v1_broad_box3_atr60_range125_body035_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r3_compression_long_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R3_COMPRESSION_LONG_V1_EXACT_202207_202606_XAUUSD_M5_r3_compression_long_v1_broad_box3_atr60_range125_body035_summary.json`
- Order activity: `{"rows": 359, "actions": {"GUARD_BLOCK": 142, "ORDER_SEND_OK": 215, "ORDER_SEND_FAIL": 2}, "guard_reasons": {"direction_mode_block": 142, "pass": 215, "order_send_failed": 2}}`

## Interpretation

The baseline failed because long-side momentum entries were much worse than shorts. If a variant improves materially, it should be treated as a hypothesis for forward testing, not as a proof of profitability. The cleanest next action is to forward-observe or demo-test only the winning diagnostic variant at minimum size, with the baseline retained as the control.
