# A1 XAU M5 Momentum Continuation Variant Backtests

Generated: `2026-07-07T11:36:08.156026+00:00`
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
| `noop_parity_box2` | `344` | `57.56%` | `16076.85` | `3.09` | `1 920.33 (12.06%)` | `0` | `16076.85` | `diagnostic_only` |
| `noop_parity_broad` | `205` | `60.98%` | `11466.34` | `3.63` | `1 720.10 (13.44%)` | `0` | `11466.34` | `diagnostic_only` |

## Winner Status

- Status: `DIAGNOSTIC_WINNER_NOT_PROMOTED`
- Note: This is a backtest-window diagnostic. Do not promote without fresh forward evidence.

## Artifacts

### `noop_parity_box2`

- Label: No-op parity rerun on h4_d1_long_best_box2_atr80
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_d1_noop_session_parity_audit_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_D1_NOOP_SESSION_PARITY_AUDIT_202207_202606_XAUUSD_M5_noop_parity_box2.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_d1_noop_session_parity_audit_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_D1_NOOP_SESSION_PARITY_AUDIT_202207_202606_XAUUSD_M5_noop_parity_box2_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_d1_noop_session_parity_audit_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_D1_NOOP_SESSION_PARITY_AUDIT_202207_202606_XAUUSD_M5_noop_parity_box2_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_d1_noop_session_parity_audit_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_D1_NOOP_SESSION_PARITY_AUDIT_202207_202606_XAUUSD_M5_noop_parity_box2_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_d1_noop_session_parity_audit_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_D1_NOOP_SESSION_PARITY_AUDIT_202207_202606_XAUUSD_M5_noop_parity_box2_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_d1_noop_session_parity_audit_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_D1_NOOP_SESSION_PARITY_AUDIT_202207_202606_XAUUSD_M5_noop_parity_box2_summary.json`
- Order activity: `{"rows": 633, "actions": {"GUARD_BLOCK": 285, "ORDER_SEND_OK": 344, "ORDER_SEND_FAIL": 4}, "guard_reasons": {"direction_mode_block": 261, "pass": 344, "blocked_entry_day_hour": 24, "order_send_failed": 4}}`

### `noop_parity_broad`

- Label: No-op parity rerun on h4_d1_long_broad_box3_atr60
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_d1_noop_session_parity_audit_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_D1_NOOP_SESSION_PARITY_AUDIT_202207_202606_XAUUSD_M5_noop_parity_broad.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_d1_noop_session_parity_audit_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_D1_NOOP_SESSION_PARITY_AUDIT_202207_202606_XAUUSD_M5_noop_parity_broad_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_d1_noop_session_parity_audit_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_D1_NOOP_SESSION_PARITY_AUDIT_202207_202606_XAUUSD_M5_noop_parity_broad_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_d1_noop_session_parity_audit_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_D1_NOOP_SESSION_PARITY_AUDIT_202207_202606_XAUUSD_M5_noop_parity_broad_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_d1_noop_session_parity_audit_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_D1_NOOP_SESSION_PARITY_AUDIT_202207_202606_XAUUSD_M5_noop_parity_broad_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_d1_noop_session_parity_audit_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_D1_NOOP_SESSION_PARITY_AUDIT_202207_202606_XAUUSD_M5_noop_parity_broad_summary.json`
- Order activity: `{"rows": 359, "actions": {"GUARD_BLOCK": 152, "ORDER_SEND_OK": 205, "ORDER_SEND_FAIL": 2}, "guard_reasons": {"direction_mode_block": 139, "pass": 205, "blocked_entry_day_hour": 13, "order_send_failed": 2}}`

## Interpretation

The baseline failed because long-side momentum entries were much worse than shorts. If a variant improves materially, it should be treated as a hypothesis for forward testing, not as a proof of profitability. The cleanest next action is to forward-observe or demo-test only the winning diagnostic variant at minimum size, with the baseline retained as the control.
