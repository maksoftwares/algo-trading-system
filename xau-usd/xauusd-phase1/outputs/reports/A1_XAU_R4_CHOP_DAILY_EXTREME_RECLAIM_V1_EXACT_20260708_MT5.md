# A1 XAU M5 Momentum Continuation Variant Backtests

Generated: `2026-07-08T17:51:38.570336+00:00`
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
| `r4_chop_daily_extreme_reclaim_v1_liquid` | `200` | `33.5%` | `-311.76` | `0.78` | `509.13 (45.79%)` | `11.52` | `-323.28` | `fail` |

## Winner Status

- Status: `NO_VARIANT_CLEARS_MINIMUM_BAR`
- Note: Positive diagnostic variants still need forward confirmation before runtime promotion.

## Artifacts

### `r4_chop_daily_extreme_reclaim_v1_liquid`

- Label: R4 chop-only daily extreme reclaim, liquid session, both directions, fixed 2R
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_daily_extreme_reclaim_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_DAILY_EXTREME_RECLAIM_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_daily_extreme_reclaim_v1_liquid.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_daily_extreme_reclaim_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_DAILY_EXTREME_RECLAIM_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_daily_extreme_reclaim_v1_liquid_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_daily_extreme_reclaim_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_DAILY_EXTREME_RECLAIM_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_daily_extreme_reclaim_v1_liquid_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_daily_extreme_reclaim_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_DAILY_EXTREME_RECLAIM_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_daily_extreme_reclaim_v1_liquid_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_daily_extreme_reclaim_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_DAILY_EXTREME_RECLAIM_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_daily_extreme_reclaim_v1_liquid_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r4_chop_daily_extreme_reclaim_v1_exact_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R4_CHOP_DAILY_EXTREME_RECLAIM_V1_EXACT_202207_202606_XAUUSD_M5_r4_chop_daily_extreme_reclaim_v1_liquid_summary.json`
- Order activity: `{"rows": 682, "actions": {"GUARD_BLOCK": 482, "ORDER_SEND_OK": 200}, "guard_reasons": {"regime_router_block_r4_chop_only_state_downtrend": 64, "regime_router_block_r4_chop_only_state_shock": 182, "regime_router_block_r4_chop_only_state_compression": 62, "pass": 200, "regime_router_block_r4_chop_only_state_uptrend": 174}}`

## Interpretation

The baseline failed because long-side momentum entries were much worse than shorts. If a variant improves materially, it should be treated as a hypothesis for forward testing, not as a proof of profitability. The cleanest next action is to forward-observe or demo-test only the winning diagnostic variant at minimum size, with the baseline retained as the control.
