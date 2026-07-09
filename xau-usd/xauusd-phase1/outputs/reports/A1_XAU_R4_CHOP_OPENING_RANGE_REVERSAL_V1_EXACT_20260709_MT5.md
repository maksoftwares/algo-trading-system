# A1 XAU M5 Momentum Continuation Variant Backtests

Generated: `2026-07-09T07:49:05.506284+00:00`
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
| `r4_chop_orrev_london_firm_both` | `578` | `33.22%` | `125.16` | `1.08` | `121.99 (11.49%)` | `50.27` | `74.89` | `diagnostic_only` |
| `r4_chop_orrev_london_firm_long` | `286` | `34.62%` | `70.89` | `1.09` | `119.06 (11.05%)` | `0` | `70.89` | `diagnostic_only` |
| `r4_chop_orrev_london_firm_short` | `336` | `32.14%` | `71.31` | `1.08` | `121.22 (11.54%)` | `71.31` | `0` | `diagnostic_only` |

## Winner Status

- Status: `NO_VARIANT_CLEARS_MINIMUM_BAR`
- Note: Positive diagnostic variants still need forward confirmation before runtime promotion.

## Artifacts

### `r4_chop_orrev_london_firm_both`

- Label: R4 chop-only London opening-range reversal, both directions, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_orrev_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_ORREV_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_orrev_london_firm_both.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_orrev_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_ORREV_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_orrev_london_firm_both_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_orrev_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_ORREV_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_orrev_london_firm_both_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_orrev_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_ORREV_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_orrev_london_firm_both_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_orrev_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_ORREV_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_orrev_london_firm_both_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_orrev_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_ORREV_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_orrev_london_firm_both_summary.json`
- Order activity: `{"rows": 2667, "actions": {"GUARD_BLOCK": 2089, "ORDER_SEND_OK": 578}, "guard_reasons": {"regime_router_block_r4_chop_only_state_downtrend": 300, "regime_router_block_r4_chop_only_state_shock": 397, "pass": 578, "own_position_exists": 363, "regime_router_block_r4_chop_only_state_compression": 266, "regime_router_block_r4_chop_only_state_uptrend": 621, "estimated_cost_r_too_high": 129, "spread_too_high": 2, "stop_ceiling_exceeded": 11}}`

### `r4_chop_orrev_london_firm_long`

- Label: R4 chop-only London opening-range reversal, long-only, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_orrev_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_ORREV_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_orrev_london_firm_long.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_orrev_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_ORREV_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_orrev_london_firm_long_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_orrev_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_ORREV_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_orrev_london_firm_long_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_orrev_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_ORREV_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_orrev_london_firm_long_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_orrev_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_ORREV_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_orrev_london_firm_long_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_orrev_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_ORREV_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_orrev_london_firm_long_summary.json`
- Order activity: `{"rows": 2667, "actions": {"GUARD_BLOCK": 2381, "ORDER_SEND_OK": 286}, "guard_reasons": {"regime_router_block_r4_chop_only_state_downtrend": 138, "direction_mode_block": 1433, "pass": 286, "own_position_exists": 131, "regime_router_block_r4_chop_only_state_compression": 141, "regime_router_block_r4_chop_only_state_shock": 175, "regime_router_block_r4_chop_only_state_uptrend": 281, "estimated_cost_r_too_high": 75, "spread_too_high": 2, "stop_ceiling_exceeded": 5}}`

### `r4_chop_orrev_london_firm_short`

- Label: R4 chop-only London opening-range reversal, short-only, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_orrev_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_ORREV_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_orrev_london_firm_short.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_orrev_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_ORREV_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_orrev_london_firm_short_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_orrev_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_ORREV_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_orrev_london_firm_short_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_orrev_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_ORREV_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_orrev_london_firm_short_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_orrev_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_ORREV_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_orrev_london_firm_short_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_orrev_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_ORREV_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_orrev_london_firm_short_summary.json`
- Order activity: `{"rows": 2667, "actions": {"GUARD_BLOCK": 2331, "ORDER_SEND_OK": 336}, "guard_reasons": {"direction_mode_block": 1234, "regime_router_block_r4_chop_only_state_downtrend": 162, "regime_router_block_r4_chop_only_state_shock": 222, "pass": 336, "own_position_exists": 188, "regime_router_block_r4_chop_only_state_compression": 125, "regime_router_block_r4_chop_only_state_uptrend": 340, "estimated_cost_r_too_high": 54, "stop_ceiling_exceeded": 6}}`

## Interpretation

The baseline failed because long-side momentum entries were much worse than shorts. If a variant improves materially, it should be treated as a hypothesis for forward testing, not as a proof of profitability. The cleanest next action is to forward-observe or demo-test only the winning diagnostic variant at minimum size, with the baseline retained as the control.
