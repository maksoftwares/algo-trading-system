# A1 XAU M5 Momentum Continuation Variant Backtests

Generated: `2026-07-08T08:05:12.267794+00:00`
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
| `prevhealth_box2_third_entry_quality` | `209` | `65.55%` | `13962.12` | `4.8` | `1 733.37 (12.89%)` | `0` | `13962.12` | `diagnostic_only` |

## Winner Status

- Status: `DIAGNOSTIC_WINNER_NOT_PROMOTED`
- Note: This is a backtest-window diagnostic. Do not promote without fresh forward evidence.

## Artifacts

### `prevhealth_box2_third_entry_quality`

- Label: H4/D1 box2 supportive + previous-month health gate + third-entry H4 quality gate
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_box2_health_third_entry_quality_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_BOX2_HEALTH_THIRD_ENTRY_QUALITY_EXACT_202207_202606_XAUUSD_M5_prevhealth_box2_third_entry_quality.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_box2_health_third_entry_quality_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_BOX2_HEALTH_THIRD_ENTRY_QUALITY_EXACT_202207_202606_XAUUSD_M5_prevhealth_box2_third_entry_quality_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_box2_health_third_entry_quality_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_BOX2_HEALTH_THIRD_ENTRY_QUALITY_EXACT_202207_202606_XAUUSD_M5_prevhealth_box2_third_entry_quality_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_box2_health_third_entry_quality_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_BOX2_HEALTH_THIRD_ENTRY_QUALITY_EXACT_202207_202606_XAUUSD_M5_prevhealth_box2_third_entry_quality_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_box2_health_third_entry_quality_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_BOX2_HEALTH_THIRD_ENTRY_QUALITY_EXACT_202207_202606_XAUUSD_M5_prevhealth_box2_third_entry_quality_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_h4_box2_health_third_entry_quality_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_H4_BOX2_HEALTH_THIRD_ENTRY_QUALITY_EXACT_202207_202606_XAUUSD_M5_prevhealth_box2_third_entry_quality_summary.json`
- Order activity: `{"rows": 633, "actions": {"GUARD_BLOCK": 421, "ORDER_SEND_OK": 209, "ORDER_SEND_FAIL": 3}, "guard_reasons": {"direction_mode_block": 261, "h4_d1_supportive_state_guard": 112, "pass": 209, "blocked_entry_day_hour": 24, "h4_d1_third_entry_quality_gate": 7, "h4_d1_previous_month_health_gate": 17, "order_send_failed": 3}}`

## Interpretation

The baseline failed because long-side momentum entries were much worse than shorts. If a variant improves materially, it should be treated as a hypothesis for forward testing, not as a proof of profitability. The cleanest next action is to forward-observe or demo-test only the winning diagnostic variant at minimum size, with the baseline retained as the control.
