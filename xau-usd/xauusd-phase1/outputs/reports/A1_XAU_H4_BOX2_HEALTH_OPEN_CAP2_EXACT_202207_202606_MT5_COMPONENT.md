# A1 XAU M5 Momentum Continuation Variant Backtests

Generated: `2026-07-08T07:47:42.733565+00:00`
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
| `prevhealth_box2_open_cap2` | `70` | `57.14%` | `3589.3` | `3.46` | `587.67 (22.60%)` | `0` | `3589.3` | `diagnostic_only` |

## Winner Status

- Status: `DIAGNOSTIC_WINNER_NOT_PROMOTED`
- Note: This is a backtest-window diagnostic. Do not promote without fresh forward evidence.

## Artifacts

### `prevhealth_box2_open_cap2`

- Label: H4/D1 box2 supportive + previous-month health gate + max 2 open positions
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_box2_health_open_cap2_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_BOX2_HEALTH_OPEN_CAP2_EXACT_202207_202606_XAUUSD_M5_prevhealth_box2_open_cap2.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_box2_health_open_cap2_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_BOX2_HEALTH_OPEN_CAP2_EXACT_202207_202606_XAUUSD_M5_prevhealth_box2_open_cap2_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_box2_health_open_cap2_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_BOX2_HEALTH_OPEN_CAP2_EXACT_202207_202606_XAUUSD_M5_prevhealth_box2_open_cap2_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_box2_health_open_cap2_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_BOX2_HEALTH_OPEN_CAP2_EXACT_202207_202606_XAUUSD_M5_prevhealth_box2_open_cap2_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_box2_health_open_cap2_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_BOX2_HEALTH_OPEN_CAP2_EXACT_202207_202606_XAUUSD_M5_prevhealth_box2_open_cap2_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_box2_health_open_cap2_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_BOX2_HEALTH_OPEN_CAP2_EXACT_202207_202606_XAUUSD_M5_prevhealth_box2_open_cap2_summary.json`
- Order activity: `{"rows": 633, "actions": {"GUARD_BLOCK": 562, "ORDER_SEND_OK": 70, "ORDER_SEND_FAIL": 1}, "guard_reasons": {"direction_mode_block": 261, "h4_d1_supportive_state_guard": 112, "pass": 70, "max_open_positions_reached": 145, "blocked_entry_day_hour": 24, "h4_d1_previous_month_health_gate": 20, "order_send_failed": 1}}`

## Interpretation

The baseline failed because long-side momentum entries were much worse than shorts. If a variant improves materially, it should be treated as a hypothesis for forward testing, not as a proof of profitability. The cleanest next action is to forward-observe or demo-test only the winning diagnostic variant at minimum size, with the baseline retained as the control.
