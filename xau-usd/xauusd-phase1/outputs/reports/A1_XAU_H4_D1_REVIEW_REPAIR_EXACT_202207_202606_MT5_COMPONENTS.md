# A1 XAU M5 Momentum Continuation Variant Backtests

Generated: `2026-07-07T11:40:07.806523+00:00`
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
| `supportive_guard_box2` | `233` | `63.52%` | `14475.67` | `4.41` | `1 733.37 (12.41%)` | `0` | `14475.67` | `diagnostic_only` |
| `supportive_guard_broad` | `158` | `65.19%` | `10674.07` | `4.15` | `1 720.10 (14.58%)` | `0` | `10674.07` | `diagnostic_only` |
| `weekly_loss_governor_box2` | `341` | `57.18%` | `15419.71` | `3.01` | `1 786.64 (11.22%)` | `0` | `15419.71` | `diagnostic_only` |
| `weekly_loss_governor_broad` | `205` | `60.98%` | `11466.34` | `3.63` | `1 720.10 (13.44%)` | `0` | `11466.34` | `diagnostic_only` |

## Winner Status

- Status: `DIAGNOSTIC_WINNER_NOT_PROMOTED`
- Note: This is a backtest-window diagnostic. Do not promote without fresh forward evidence.

## Artifacts

### `supportive_guard_box2`

- Label: H4/D1 supportive-state guard: D1 close[1] > EMA20[1] and EMA20[1] >= EMA20[6] on h4_d1_long_best_box2_atr80
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_d1_review_repair_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_D1_REVIEW_REPAIR_202207_202606_XAUUSD_M5_supportive_guard_box2.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_d1_review_repair_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_D1_REVIEW_REPAIR_202207_202606_XAUUSD_M5_supportive_guard_box2_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_d1_review_repair_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_D1_REVIEW_REPAIR_202207_202606_XAUUSD_M5_supportive_guard_box2_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_d1_review_repair_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_D1_REVIEW_REPAIR_202207_202606_XAUUSD_M5_supportive_guard_box2_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_d1_review_repair_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_D1_REVIEW_REPAIR_202207_202606_XAUUSD_M5_supportive_guard_box2_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_d1_review_repair_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_D1_REVIEW_REPAIR_202207_202606_XAUUSD_M5_supportive_guard_box2_summary.json`
- Order activity: `{"rows": 633, "actions": {"GUARD_BLOCK": 397, "ORDER_SEND_OK": 233, "ORDER_SEND_FAIL": 3}, "guard_reasons": {"direction_mode_block": 261, "h4_d1_supportive_state_guard": 112, "pass": 233, "blocked_entry_day_hour": 24, "order_send_failed": 3}}`

### `supportive_guard_broad`

- Label: H4/D1 supportive-state guard: D1 close[1] > EMA20[1] and EMA20[1] >= EMA20[6] on h4_d1_long_broad_box3_atr60
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_d1_review_repair_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_D1_REVIEW_REPAIR_202207_202606_XAUUSD_M5_supportive_guard_broad.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_d1_review_repair_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_D1_REVIEW_REPAIR_202207_202606_XAUUSD_M5_supportive_guard_broad_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_d1_review_repair_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_D1_REVIEW_REPAIR_202207_202606_XAUUSD_M5_supportive_guard_broad_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_d1_review_repair_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_D1_REVIEW_REPAIR_202207_202606_XAUUSD_M5_supportive_guard_broad_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_d1_review_repair_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_D1_REVIEW_REPAIR_202207_202606_XAUUSD_M5_supportive_guard_broad_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_d1_review_repair_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_D1_REVIEW_REPAIR_202207_202606_XAUUSD_M5_supportive_guard_broad_summary.json`
- Order activity: `{"rows": 359, "actions": {"GUARD_BLOCK": 199, "ORDER_SEND_OK": 158, "ORDER_SEND_FAIL": 2}, "guard_reasons": {"direction_mode_block": 139, "h4_d1_supportive_state_guard": 47, "pass": 158, "blocked_entry_day_hour": 13, "order_send_failed": 2}}`

### `weekly_loss_governor_box2`

- Label: H4/D1 weekly loss governor: block after closed weekly component PnL <= -150 USD on h4_d1_long_best_box2_atr80
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_d1_review_repair_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_D1_REVIEW_REPAIR_202207_202606_XAUUSD_M5_weekly_loss_governor_box2.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_d1_review_repair_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_D1_REVIEW_REPAIR_202207_202606_XAUUSD_M5_weekly_loss_governor_box2_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_d1_review_repair_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_D1_REVIEW_REPAIR_202207_202606_XAUUSD_M5_weekly_loss_governor_box2_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_d1_review_repair_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_D1_REVIEW_REPAIR_202207_202606_XAUUSD_M5_weekly_loss_governor_box2_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_d1_review_repair_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_D1_REVIEW_REPAIR_202207_202606_XAUUSD_M5_weekly_loss_governor_box2_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_d1_review_repair_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_D1_REVIEW_REPAIR_202207_202606_XAUUSD_M5_weekly_loss_governor_box2_summary.json`
- Order activity: `{"rows": 633, "actions": {"GUARD_BLOCK": 288, "ORDER_SEND_OK": 341, "ORDER_SEND_FAIL": 4}, "guard_reasons": {"direction_mode_block": 261, "pass": 341, "blocked_entry_day_hour": 24, "order_send_failed": 4, "h4_d1_weekly_loss_governor": 3}}`

### `weekly_loss_governor_broad`

- Label: H4/D1 weekly loss governor: block after closed weekly component PnL <= -150 USD on h4_d1_long_broad_box3_atr60
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_d1_review_repair_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_D1_REVIEW_REPAIR_202207_202606_XAUUSD_M5_weekly_loss_governor_broad.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_d1_review_repair_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_D1_REVIEW_REPAIR_202207_202606_XAUUSD_M5_weekly_loss_governor_broad_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_d1_review_repair_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_D1_REVIEW_REPAIR_202207_202606_XAUUSD_M5_weekly_loss_governor_broad_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_d1_review_repair_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_D1_REVIEW_REPAIR_202207_202606_XAUUSD_M5_weekly_loss_governor_broad_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_d1_review_repair_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_D1_REVIEW_REPAIR_202207_202606_XAUUSD_M5_weekly_loss_governor_broad_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_d1_review_repair_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_D1_REVIEW_REPAIR_202207_202606_XAUUSD_M5_weekly_loss_governor_broad_summary.json`
- Order activity: `{"rows": 359, "actions": {"GUARD_BLOCK": 152, "ORDER_SEND_OK": 205, "ORDER_SEND_FAIL": 2}, "guard_reasons": {"direction_mode_block": 139, "pass": 205, "blocked_entry_day_hour": 13, "order_send_failed": 2}}`

## Interpretation

The baseline failed because long-side momentum entries were much worse than shorts. If a variant improves materially, it should be treated as a hypothesis for forward testing, not as a proof of profitability. The cleanest next action is to forward-observe or demo-test only the winning diagnostic variant at minimum size, with the baseline retained as the control.
