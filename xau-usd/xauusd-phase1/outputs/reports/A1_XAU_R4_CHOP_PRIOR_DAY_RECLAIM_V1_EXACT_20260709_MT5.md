# A1 XAU M5 Momentum Continuation Variant Backtests

Generated: `2026-07-09T06:49:08.376453+00:00`
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
| `r4_chop_prior_day_reclaim_v1_both` | `526` | `33.84%` | `95.06` | `1.06` | `148.67 (13.08%)` | `-1.86` | `96.92` | `diagnostic_only` |
| `r4_chop_prior_day_reclaim_v1_long` | `278` | `35.25%` | `73.93` | `1.09` | `123.93 (11.32%)` | `0` | `73.93` | `diagnostic_only` |
| `r4_chop_prior_day_reclaim_v1_short` | `274` | `30.66%` | `-17.53` | `0.98` | `100.15 (9.67%)` | `-17.53` | `0` | `fail` |

## Winner Status

- Status: `NO_VARIANT_CLEARS_MINIMUM_BAR`
- Note: Positive diagnostic variants still need forward confirmation before runtime promotion.

## Artifacts

### `r4_chop_prior_day_reclaim_v1_both`

- Label: R4 chop-only prior-day high/low reclaim reversal, both directions, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_prior_day_reclaim_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_prior_day_reclaim_v1_both.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_prior_day_reclaim_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_prior_day_reclaim_v1_both_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_prior_day_reclaim_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_prior_day_reclaim_v1_both_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_prior_day_reclaim_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_prior_day_reclaim_v1_both_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_prior_day_reclaim_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_prior_day_reclaim_v1_both_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_prior_day_reclaim_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_prior_day_reclaim_v1_both_summary.json`
- Order activity: `{"rows": 2346, "actions": {"GUARD_BLOCK": 1820, "ORDER_SEND_OK": 526}, "guard_reasons": {"regime_router_block_r4_chop_only_state_downtrend": 200, "regime_router_block_r4_chop_only_state_compression": 317, "regime_router_block_r4_chop_only_state_shock": 430, "pass": 526, "own_position_exists": 304, "stop_ceiling_exceeded": 30, "regime_router_block_r4_chop_only_state_uptrend": 462, "estimated_cost_r_too_high": 77}}`

### `r4_chop_prior_day_reclaim_v1_long`

- Label: R4 chop-only prior-day-low reclaim reversal, long-only, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_prior_day_reclaim_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_prior_day_reclaim_v1_long.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_prior_day_reclaim_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_prior_day_reclaim_v1_long_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_prior_day_reclaim_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_prior_day_reclaim_v1_long_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_prior_day_reclaim_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_prior_day_reclaim_v1_long_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_prior_day_reclaim_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_prior_day_reclaim_v1_long_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_prior_day_reclaim_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_prior_day_reclaim_v1_long_summary.json`
- Order activity: `{"rows": 2346, "actions": {"GUARD_BLOCK": 2068, "ORDER_SEND_OK": 278}, "guard_reasons": {"regime_router_block_r4_chop_only_state_downtrend": 154, "direction_mode_block": 1252, "regime_router_block_r4_chop_only_state_shock": 210, "pass": 278, "regime_router_block_r4_chop_only_state_compression": 136, "own_position_exists": 136, "regime_router_block_r4_chop_only_state_uptrend": 129, "stop_ceiling_exceeded": 15, "estimated_cost_r_too_high": 36}}`

### `r4_chop_prior_day_reclaim_v1_short`

- Label: R4 chop-only prior-day-high reclaim reversal, short-only, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_prior_day_reclaim_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_prior_day_reclaim_v1_short.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_prior_day_reclaim_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_prior_day_reclaim_v1_short_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_prior_day_reclaim_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_prior_day_reclaim_v1_short_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_prior_day_reclaim_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_prior_day_reclaim_v1_short_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_prior_day_reclaim_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_prior_day_reclaim_v1_short_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_prior_day_reclaim_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_prior_day_reclaim_v1_short_summary.json`
- Order activity: `{"rows": 2346, "actions": {"GUARD_BLOCK": 2072, "ORDER_SEND_OK": 274}, "guard_reasons": {"direction_mode_block": 1094, "regime_router_block_r4_chop_only_state_compression": 181, "regime_router_block_r4_chop_only_state_downtrend": 46, "regime_router_block_r4_chop_only_state_shock": 220, "pass": 274, "own_position_exists": 142, "stop_ceiling_exceeded": 15, "regime_router_block_r4_chop_only_state_uptrend": 333, "estimated_cost_r_too_high": 41}}`

## Interpretation

The baseline failed because long-side momentum entries were much worse than shorts. If a variant improves materially, it should be treated as a hypothesis for forward testing, not as a proof of profitability. The cleanest next action is to forward-observe or demo-test only the winning diagnostic variant at minimum size, with the baseline retained as the control.
