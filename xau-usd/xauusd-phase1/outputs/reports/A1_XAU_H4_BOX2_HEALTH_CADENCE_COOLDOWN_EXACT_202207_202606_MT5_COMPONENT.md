# A1 XAU M5 Momentum Continuation Variant Backtests

Generated: `2026-07-08T09:58:20.439360+00:00`
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
| `prevhealth_box2_cadence_cooldown_480` | `180` | `63.89%` | `10630.97` | `4.26` | `1 348.31 (12.87%)` | `0` | `10630.97` | `diagnostic_only` |

## Winner Status

- Status: `DIAGNOSTIC_WINNER_NOT_PROMOTED`
- Note: This is a backtest-window diagnostic. Do not promote without fresh forward evidence.

## Artifacts

### `prevhealth_box2_cadence_cooldown_480`

- Label: H4/D1 box2 supportive + previous-month health gate + 480-minute cooldown
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_box2_health_cadence_cooldown_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_BOX2_HEALTH_CADENCE_COOLDOWN_EXACT_202207_202606_XAUUSD_M5_prevhealth_box2_cadence_cooldown_480.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_box2_health_cadence_cooldown_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_BOX2_HEALTH_CADENCE_COOLDOWN_EXACT_202207_202606_XAUUSD_M5_prevhealth_box2_cadence_cooldown_480_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_box2_health_cadence_cooldown_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_BOX2_HEALTH_CADENCE_COOLDOWN_EXACT_202207_202606_XAUUSD_M5_prevhealth_box2_cadence_cooldown_480_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_box2_health_cadence_cooldown_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_BOX2_HEALTH_CADENCE_COOLDOWN_EXACT_202207_202606_XAUUSD_M5_prevhealth_box2_cadence_cooldown_480_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_box2_health_cadence_cooldown_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_BOX2_HEALTH_CADENCE_COOLDOWN_EXACT_202207_202606_XAUUSD_M5_prevhealth_box2_cadence_cooldown_480_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_box2_health_cadence_cooldown_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_BOX2_HEALTH_CADENCE_COOLDOWN_EXACT_202207_202606_XAUUSD_M5_prevhealth_box2_cadence_cooldown_480_summary.json`
- Order activity: `{"rows": 633, "actions": {"GUARD_BLOCK": 451, "ORDER_SEND_OK": 180, "ORDER_SEND_FAIL": 2}, "guard_reasons": {"direction_mode_block": 261, "h4_d1_supportive_state_guard": 112, "pass": 180, "blocked_entry_day_hour": 24, "cooldown_active": 37, "h4_d1_previous_month_health_gate": 17, "order_send_failed": 2}}`

## Interpretation

The baseline failed because long-side momentum entries were much worse than shorts. If a variant improves materially, it should be treated as a hypothesis for forward testing, not as a proof of profitability. The cleanest next action is to forward-observe or demo-test only the winning diagnostic variant at minimum size, with the baseline retained as the control.
