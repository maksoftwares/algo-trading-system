# A1 XAU M5 Momentum Continuation Variant Backtests

Generated: `2026-07-08T11:58:05.286071+00:00`
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
| `short_v4_impulse_retest_d1_nonup_h1h4` | `287` | `32.75%` | `367.41` | `1.35` | `276.53 (25.29%)` | `367.41` | `0` | `diagnostic_only` |
| `short_v4_impulse_retest_d1_structural_h1h4` | `180` | `40.0%` | `452.16` | `1.78` | `90.13 (8.30%)` | `452.16` | `0` | `diagnostic_only` |
| `short_v4_impulse_retest_d1_nonup_h1_only` | `307` | `32.57%` | `333.44` | `1.29` | `282.11 (25.80%)` | `333.44` | `0` | `diagnostic_only` |

## Winner Status

- Status: `DIAGNOSTIC_WINNER_NOT_PROMOTED`
- Note: This is a backtest-window diagnostic. Do not promote without fresh forward evidence.

## Artifacts

### `short_v4_impulse_retest_d1_nonup_h1h4`

- Label: V4 downside impulse retest: D1 non-up plus H1/H4 downtrend
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_downside_impulse_retest_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_DOWNSIDE_IMPULSE_RETEST_202207_202606_XAUUSD_M5_short_v4_impulse_retest_d1_nonup_h1h4.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_downside_impulse_retest_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_DOWNSIDE_IMPULSE_RETEST_202207_202606_XAUUSD_M5_short_v4_impulse_retest_d1_nonup_h1h4_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_downside_impulse_retest_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_DOWNSIDE_IMPULSE_RETEST_202207_202606_XAUUSD_M5_short_v4_impulse_retest_d1_nonup_h1h4_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_downside_impulse_retest_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_DOWNSIDE_IMPULSE_RETEST_202207_202606_XAUUSD_M5_short_v4_impulse_retest_d1_nonup_h1h4_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_downside_impulse_retest_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_DOWNSIDE_IMPULSE_RETEST_202207_202606_XAUUSD_M5_short_v4_impulse_retest_d1_nonup_h1h4_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_downside_impulse_retest_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_DOWNSIDE_IMPULSE_RETEST_202207_202606_XAUUSD_M5_short_v4_impulse_retest_d1_nonup_h1h4_summary.json`
- Order activity: `{"rows": 4914, "actions": {"ORDER_SEND_OK": 287, "GUARD_BLOCK": 4627}, "guard_reasons": {"pass": 287, "own_position_exists": 539, "h1_trend_filter_block": 3267, "h4_trend_filter_block": 555, "d1_support_state_gate": 91, "estimated_cost_r_too_high": 119, "stop_ceiling_exceeded": 55, "spread_too_high": 1}}`

### `short_v4_impulse_retest_d1_structural_h1h4`

- Label: V4 downside impulse retest: D1 EMA50 structural down plus H1/H4 downtrend
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_downside_impulse_retest_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_DOWNSIDE_IMPULSE_RETEST_202207_202606_XAUUSD_M5_short_v4_impulse_retest_d1_structural_h1h4.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_downside_impulse_retest_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_DOWNSIDE_IMPULSE_RETEST_202207_202606_XAUUSD_M5_short_v4_impulse_retest_d1_structural_h1h4_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_downside_impulse_retest_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_DOWNSIDE_IMPULSE_RETEST_202207_202606_XAUUSD_M5_short_v4_impulse_retest_d1_structural_h1h4_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_downside_impulse_retest_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_DOWNSIDE_IMPULSE_RETEST_202207_202606_XAUUSD_M5_short_v4_impulse_retest_d1_structural_h1h4_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_downside_impulse_retest_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_DOWNSIDE_IMPULSE_RETEST_202207_202606_XAUUSD_M5_short_v4_impulse_retest_d1_structural_h1h4_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_downside_impulse_retest_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_DOWNSIDE_IMPULSE_RETEST_202207_202606_XAUUSD_M5_short_v4_impulse_retest_d1_structural_h1h4_summary.json`
- Order activity: `{"rows": 4914, "actions": {"ORDER_SEND_OK": 180, "GUARD_BLOCK": 4734}, "guard_reasons": {"pass": 180, "own_position_exists": 381, "h1_trend_filter_block": 3267, "h4_trend_filter_block": 555, "d1_support_state_gate": 416, "estimated_cost_r_too_high": 75, "stop_ceiling_exceeded": 40}}`

### `short_v4_impulse_retest_d1_nonup_h1_only`

- Label: V4 downside impulse retest: D1 non-up plus H1 downtrend only
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_downside_impulse_retest_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_DOWNSIDE_IMPULSE_RETEST_202207_202606_XAUUSD_M5_short_v4_impulse_retest_d1_nonup_h1_only.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_downside_impulse_retest_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_DOWNSIDE_IMPULSE_RETEST_202207_202606_XAUUSD_M5_short_v4_impulse_retest_d1_nonup_h1_only_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_downside_impulse_retest_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_DOWNSIDE_IMPULSE_RETEST_202207_202606_XAUUSD_M5_short_v4_impulse_retest_d1_nonup_h1_only_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_downside_impulse_retest_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_DOWNSIDE_IMPULSE_RETEST_202207_202606_XAUUSD_M5_short_v4_impulse_retest_d1_nonup_h1_only_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_downside_impulse_retest_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_DOWNSIDE_IMPULSE_RETEST_202207_202606_XAUUSD_M5_short_v4_impulse_retest_d1_nonup_h1_only_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_downside_impulse_retest_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_DOWNSIDE_IMPULSE_RETEST_202207_202606_XAUUSD_M5_short_v4_impulse_retest_d1_nonup_h1_only_summary.json`
- Order activity: `{"rows": 4914, "actions": {"ORDER_SEND_OK": 307, "GUARD_BLOCK": 4607}, "guard_reasons": {"pass": 307, "own_position_exists": 568, "h1_trend_filter_block": 3267, "d1_support_state_gate": 578, "estimated_cost_r_too_high": 133, "stop_ceiling_exceeded": 57, "spread_too_high": 4}}`

## Interpretation

The baseline failed because long-side momentum entries were much worse than shorts. If a variant improves materially, it should be treated as a hypothesis for forward testing, not as a proof of profitability. The cleanest next action is to forward-observe or demo-test only the winning diagnostic variant at minimum size, with the baseline retained as the control.
