# A1 XAU M5 Momentum Continuation Variant Backtests

Generated: `2026-07-07T20:42:25.326922+00:00`
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
| `short_hedge_v1_break_run_control` | `445` | `32.13%` | `208.0` | `1.11` | `331.21 (30.32%)` | `208.0` | `0` | `diagnostic_only` |
| `short_hedge_v2_breakdown_retest` | `329` | `32.83%` | `441.42` | `1.38` | `257.03 (23.57%)` | `441.42` | `0` | `diagnostic_only` |
| `short_hedge_v3_prior_high_sweep_reclaim` | `350` | `33.43%` | `43.37` | `1.03` | `251.16 (23.33%)` | `43.37` | `0` | `diagnostic_only` |

## Winner Status

- Status: `DIAGNOSTIC_WINNER_NOT_PROMOTED`
- Note: This is a backtest-window diagnostic. Do not promote without fresh forward evidence.

## Artifacts

### `short_hedge_v1_break_run_control`

- Label: Short hedge V1 control: D1 bearish + H1/H4 break-and-run short, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_hedge_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_HEDGE_202207_202606_XAUUSD_M5_short_hedge_v1_break_run_control.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_hedge_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_HEDGE_202207_202606_XAUUSD_M5_short_hedge_v1_break_run_control_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_hedge_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_HEDGE_202207_202606_XAUUSD_M5_short_hedge_v1_break_run_control_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_hedge_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_HEDGE_202207_202606_XAUUSD_M5_short_hedge_v1_break_run_control_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_hedge_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_HEDGE_202207_202606_XAUUSD_M5_short_hedge_v1_break_run_control_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_hedge_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_HEDGE_202207_202606_XAUUSD_M5_short_hedge_v1_break_run_control_summary.json`
- Order activity: `{"rows": 24379, "actions": {"ORDER_SEND_OK": 445, "GUARD_BLOCK": 23934}, "guard_reasons": {"pass": 445, "own_position_exists": 1020, "direction_mode_block": 12349, "h1_trend_filter_block": 8319, "h4_trend_filter_block": 1365, "d1_support_state_gate": 581, "estimated_cost_r_too_high": 165, "stop_ceiling_exceeded": 135}}`

### `short_hedge_v2_breakdown_retest`

- Label: Short hedge V2: D1 bearish + H1/H4 breakdown-retest short, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_hedge_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_HEDGE_202207_202606_XAUUSD_M5_short_hedge_v2_breakdown_retest.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_hedge_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_HEDGE_202207_202606_XAUUSD_M5_short_hedge_v2_breakdown_retest_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_hedge_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_HEDGE_202207_202606_XAUUSD_M5_short_hedge_v2_breakdown_retest_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_hedge_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_HEDGE_202207_202606_XAUUSD_M5_short_hedge_v2_breakdown_retest_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_hedge_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_HEDGE_202207_202606_XAUUSD_M5_short_hedge_v2_breakdown_retest_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_hedge_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_HEDGE_202207_202606_XAUUSD_M5_short_hedge_v2_breakdown_retest_summary.json`
- Order activity: `{"rows": 8881, "actions": {"ORDER_SEND_OK": 329, "GUARD_BLOCK": 8552}, "guard_reasons": {"pass": 329, "own_position_exists": 788, "h1_trend_filter_block": 5937, "stop_ceiling_exceeded": 103, "h4_trend_filter_block": 1082, "d1_support_state_gate": 416, "estimated_cost_r_too_high": 226}}`

### `short_hedge_v3_prior_high_sweep_reclaim`

- Label: Short hedge V3: D1 non-up prior-day-high sweep/reclaim short, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_hedge_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_HEDGE_202207_202606_XAUUSD_M5_short_hedge_v3_prior_high_sweep_reclaim.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_hedge_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_HEDGE_202207_202606_XAUUSD_M5_short_hedge_v3_prior_high_sweep_reclaim_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_hedge_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_HEDGE_202207_202606_XAUUSD_M5_short_hedge_v3_prior_high_sweep_reclaim_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_hedge_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_HEDGE_202207_202606_XAUUSD_M5_short_hedge_v3_prior_high_sweep_reclaim_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_hedge_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_HEDGE_202207_202606_XAUUSD_M5_short_hedge_v3_prior_high_sweep_reclaim_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_hedge_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_HEDGE_202207_202606_XAUUSD_M5_short_hedge_v3_prior_high_sweep_reclaim_summary.json`
- Order activity: `{"rows": 5302, "actions": {"ORDER_SEND_OK": 350, "GUARD_BLOCK": 4952}, "guard_reasons": {"pass": 350, "own_position_exists": 1381, "d1_support_state_gate": 3164, "stop_ceiling_exceeded": 50, "estimated_cost_r_too_high": 349, "spread_too_high": 8}}`

## Interpretation

The baseline failed because long-side momentum entries were much worse than shorts. If a variant improves materially, it should be treated as a hypothesis for forward testing, not as a proof of profitability. The cleanest next action is to forward-observe or demo-test only the winning diagnostic variant at minimum size, with the baseline retained as the control.
