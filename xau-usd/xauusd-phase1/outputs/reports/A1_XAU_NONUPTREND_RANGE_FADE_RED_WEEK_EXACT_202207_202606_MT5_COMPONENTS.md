# A1 XAU M5 Momentum Continuation Variant Backtests

Generated: `2026-07-07T12:19:43.080695+00:00`
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
| `nonup_daily_extreme_rr2` | `224` | `33.48%` | `-283.56` | `0.81` | `540.09 (46.33%)` | `-142.15` | `-141.41` | `fail` |
| `nonup_prior_day_reversal_rr2` | `506` | `34.19%` | `48.99` | `1.04` | `137.17 (11.63%)` | `106.77` | `-57.78` | `diagnostic_only` |
| `nonup_orrev_london_rr2` | `629` | `33.23%` | `12.69` | `1.01` | `185.61 (16.68%)` | `126.3` | `-113.61` | `diagnostic_only` |

## Winner Status

- Status: `NO_VARIANT_CLEARS_MINIMUM_BAR`
- Note: Positive diagnostic variants still need forward confirmation before runtime promotion.

## Artifacts

### `nonup_daily_extreme_rr2`

- Label: Non-uptrend daily-extreme reclaim, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_nonuptrend_range_fade_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_NONUPTREND_RANGE_FADE_202207_202606_XAUUSD_M5_nonup_daily_extreme_rr2.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_nonuptrend_range_fade_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_NONUPTREND_RANGE_FADE_202207_202606_XAUUSD_M5_nonup_daily_extreme_rr2_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_nonuptrend_range_fade_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_NONUPTREND_RANGE_FADE_202207_202606_XAUUSD_M5_nonup_daily_extreme_rr2_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_nonuptrend_range_fade_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_NONUPTREND_RANGE_FADE_202207_202606_XAUUSD_M5_nonup_daily_extreme_rr2_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_nonuptrend_range_fade_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_NONUPTREND_RANGE_FADE_202207_202606_XAUUSD_M5_nonup_daily_extreme_rr2_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_nonuptrend_range_fade_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_NONUPTREND_RANGE_FADE_202207_202606_XAUUSD_M5_nonup_daily_extreme_rr2_summary.json`
- Order activity: `{"rows": 682, "actions": {"ORDER_SEND_OK": 224, "GUARD_BLOCK": 458}, "guard_reasons": {"pass": 224, "d1_support_state_gate": 454, "blocked_entry_day_hour": 4}}`

### `nonup_prior_day_reversal_rr2`

- Label: Non-uptrend prior-day high/low reversal, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_nonuptrend_range_fade_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_NONUPTREND_RANGE_FADE_202207_202606_XAUUSD_M5_nonup_prior_day_reversal_rr2.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_nonuptrend_range_fade_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_NONUPTREND_RANGE_FADE_202207_202606_XAUUSD_M5_nonup_prior_day_reversal_rr2_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_nonuptrend_range_fade_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_NONUPTREND_RANGE_FADE_202207_202606_XAUUSD_M5_nonup_prior_day_reversal_rr2_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_nonuptrend_range_fade_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_NONUPTREND_RANGE_FADE_202207_202606_XAUUSD_M5_nonup_prior_day_reversal_rr2_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_nonuptrend_range_fade_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_NONUPTREND_RANGE_FADE_202207_202606_XAUUSD_M5_nonup_prior_day_reversal_rr2_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_nonuptrend_range_fade_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_NONUPTREND_RANGE_FADE_202207_202606_XAUUSD_M5_nonup_prior_day_reversal_rr2_summary.json`
- Order activity: `{"rows": 2051, "actions": {"ORDER_SEND_OK": 506, "GUARD_BLOCK": 1545}, "guard_reasons": {"pass": 506, "own_position_exists": 321, "d1_support_state_gate": 1135, "stop_ceiling_exceeded": 32, "estimated_cost_r_too_high": 41, "blocked_entry_day_hour": 6, "spread_too_high": 10}}`

### `nonup_orrev_london_rr2`

- Label: Non-uptrend London opening-range reversal, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_nonuptrend_range_fade_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_NONUPTREND_RANGE_FADE_202207_202606_XAUUSD_M5_nonup_orrev_london_rr2.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_nonuptrend_range_fade_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_NONUPTREND_RANGE_FADE_202207_202606_XAUUSD_M5_nonup_orrev_london_rr2_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_nonuptrend_range_fade_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_NONUPTREND_RANGE_FADE_202207_202606_XAUUSD_M5_nonup_orrev_london_rr2_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_nonuptrend_range_fade_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_NONUPTREND_RANGE_FADE_202207_202606_XAUUSD_M5_nonup_orrev_london_rr2_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_nonuptrend_range_fade_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_NONUPTREND_RANGE_FADE_202207_202606_XAUUSD_M5_nonup_orrev_london_rr2_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_nonuptrend_range_fade_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_NONUPTREND_RANGE_FADE_202207_202606_XAUUSD_M5_nonup_orrev_london_rr2_summary.json`
- Order activity: `{"rows": 2667, "actions": {"ORDER_SEND_OK": 629, "GUARD_BLOCK": 2038}, "guard_reasons": {"pass": 629, "own_position_exists": 470, "d1_support_state_gate": 1443, "estimated_cost_r_too_high": 102, "spread_too_high": 1, "stop_ceiling_exceeded": 22}}`

## Interpretation

The baseline failed because long-side momentum entries were much worse than shorts. If a variant improves materially, it should be treated as a hypothesis for forward testing, not as a proof of profitability. The cleanest next action is to forward-observe or demo-test only the winning diagnostic variant at minimum size, with the baseline retained as the control.
