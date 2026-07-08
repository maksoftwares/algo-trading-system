# A1 XAU M5 Momentum Continuation Variant Backtests

Generated: `2026-07-07T22:32:07.669635+00:00`
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
| `lower_high_lh1_base` | `302` | `33.44%` | `119.96` | `1.06` | `471.58 (38.68%)` | `119.96` | `0` | `diagnostic_only` |
| `lower_high_lh2_deeper_drop` | `279` | `33.69%` | `29.83` | `1.02` | `376.28 (32.13%)` | `29.83` | `0` | `diagnostic_only` |
| `lower_high_lh3_tighter_reject` | `316` | `33.86%` | `71.98` | `1.04` | `317.25 (26.40%)` | `71.98` | `0` | `diagnostic_only` |

## Winner Status

- Status: `NO_VARIANT_CLEARS_MINIMUM_BAR`
- Note: Positive diagnostic variants still need forward confirmation before runtime promotion.

## Artifacts

### `lower_high_lh1_base`

- Label: Lower-high failed-rally base, RR2
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_lower_high_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_LOWER_HIGH_WR50_RR2_202207_202606_XAUUSD_M5_lower_high_lh1_base.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_lower_high_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_LOWER_HIGH_WR50_RR2_202207_202606_XAUUSD_M5_lower_high_lh1_base_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_lower_high_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_LOWER_HIGH_WR50_RR2_202207_202606_XAUUSD_M5_lower_high_lh1_base_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_lower_high_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_LOWER_HIGH_WR50_RR2_202207_202606_XAUUSD_M5_lower_high_lh1_base_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_lower_high_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_LOWER_HIGH_WR50_RR2_202207_202606_XAUUSD_M5_lower_high_lh1_base_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_lower_high_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_LOWER_HIGH_WR50_RR2_202207_202606_XAUUSD_M5_lower_high_lh1_base_summary.json`
- Order activity: `{"rows": 28237, "actions": {"ORDER_SEND_OK": 302, "GUARD_BLOCK": 27935}, "guard_reasons": {"pass": 302, "own_position_exists": 2837, "h1_trend_filter_block": 18199, "stop_ceiling_exceeded": 282, "estimated_cost_r_too_high": 326, "h4_trend_filter_block": 3789, "d1_support_state_gate": 2502}}`

### `lower_high_lh2_deeper_drop`

- Label: Lower-high failed-rally deeper prior drop, RR2
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_lower_high_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_LOWER_HIGH_WR50_RR2_202207_202606_XAUUSD_M5_lower_high_lh2_deeper_drop.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_lower_high_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_LOWER_HIGH_WR50_RR2_202207_202606_XAUUSD_M5_lower_high_lh2_deeper_drop_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_lower_high_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_LOWER_HIGH_WR50_RR2_202207_202606_XAUUSD_M5_lower_high_lh2_deeper_drop_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_lower_high_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_LOWER_HIGH_WR50_RR2_202207_202606_XAUUSD_M5_lower_high_lh2_deeper_drop_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_lower_high_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_LOWER_HIGH_WR50_RR2_202207_202606_XAUUSD_M5_lower_high_lh2_deeper_drop_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_lower_high_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_LOWER_HIGH_WR50_RR2_202207_202606_XAUUSD_M5_lower_high_lh2_deeper_drop_summary.json`
- Order activity: `{"rows": 28268, "actions": {"ORDER_SEND_OK": 279, "GUARD_BLOCK": 27989}, "guard_reasons": {"pass": 279, "own_position_exists": 2977, "h1_trend_filter_block": 17910, "stop_ceiling_exceeded": 336, "estimated_cost_r_too_high": 292, "h4_trend_filter_block": 3872, "d1_support_state_gate": 2602}}`

### `lower_high_lh3_tighter_reject`

- Label: Lower-high failed-rally tighter rejection, RR2
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_lower_high_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_LOWER_HIGH_WR50_RR2_202207_202606_XAUUSD_M5_lower_high_lh3_tighter_reject.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_lower_high_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_LOWER_HIGH_WR50_RR2_202207_202606_XAUUSD_M5_lower_high_lh3_tighter_reject_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_lower_high_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_LOWER_HIGH_WR50_RR2_202207_202606_XAUUSD_M5_lower_high_lh3_tighter_reject_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_lower_high_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_LOWER_HIGH_WR50_RR2_202207_202606_XAUUSD_M5_lower_high_lh3_tighter_reject_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_lower_high_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_LOWER_HIGH_WR50_RR2_202207_202606_XAUUSD_M5_lower_high_lh3_tighter_reject_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_lower_high_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_LOWER_HIGH_WR50_RR2_202207_202606_XAUUSD_M5_lower_high_lh3_tighter_reject_summary.json`
- Order activity: `{"rows": 21684, "actions": {"ORDER_SEND_OK": 316, "GUARD_BLOCK": 21368}, "guard_reasons": {"pass": 316, "own_position_exists": 2070, "h1_trend_filter_block": 14083, "estimated_cost_r_too_high": 260, "h4_trend_filter_block": 2876, "d1_support_state_gate": 1882, "stop_ceiling_exceeded": 197}}`

## Interpretation

The baseline failed because long-side momentum entries were much worse than shorts. If a variant improves materially, it should be treated as a hypothesis for forward testing, not as a proof of profitability. The cleanest next action is to forward-observe or demo-test only the winning diagnostic variant at minimum size, with the baseline retained as the control.
