# A1 XAU M5 Momentum Continuation Variant Backtests

Generated: `2026-07-07T22:10:38.796298+00:00`
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
| `short_v2_r1_d1_ema20_bearish` | `329` | `32.83%` | `441.42` | `1.38` | `257.03 (23.57%)` | `441.42` | `0` | `diagnostic_only` |
| `short_v2_r2_d1_ema20_nonup` | `393` | `33.84%` | `507.56` | `1.36` | `256.89 (23.40%)` | `507.56` | `0` | `diagnostic_only` |
| `short_v2_r3_d1_ema50_structural_down` | `242` | `36.36%` | `345.72` | `1.41` | `154.54 (14.12%)` | `345.72` | `0` | `diagnostic_only` |

## Winner Status

- Status: `DIAGNOSTIC_WINNER_NOT_PROMOTED`
- Note: This is a backtest-window diagnostic. Do not promote without fresh forward evidence.

## Artifacts

### `short_v2_r1_d1_ema20_bearish`

- Label: R1 baseline/parity: V2 D1 EMA20 bearish gate, RR 2.00
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_v2_robustness_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_V2_ROBUSTNESS_202207_202606_XAUUSD_M5_short_v2_r1_d1_ema20_bearish.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_v2_robustness_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_V2_ROBUSTNESS_202207_202606_XAUUSD_M5_short_v2_r1_d1_ema20_bearish_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_v2_robustness_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_V2_ROBUSTNESS_202207_202606_XAUUSD_M5_short_v2_r1_d1_ema20_bearish_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_v2_robustness_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_V2_ROBUSTNESS_202207_202606_XAUUSD_M5_short_v2_r1_d1_ema20_bearish_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_v2_robustness_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_V2_ROBUSTNESS_202207_202606_XAUUSD_M5_short_v2_r1_d1_ema20_bearish_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_v2_robustness_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_V2_ROBUSTNESS_202207_202606_XAUUSD_M5_short_v2_r1_d1_ema20_bearish_summary.json`
- Order activity: `{"rows": 8881, "actions": {"ORDER_SEND_OK": 329, "GUARD_BLOCK": 8552}, "guard_reasons": {"pass": 329, "own_position_exists": 788, "h1_trend_filter_block": 5937, "stop_ceiling_exceeded": 103, "h4_trend_filter_block": 1082, "d1_support_state_gate": 416, "estimated_cost_r_too_high": 226}}`

### `short_v2_r2_d1_ema20_nonup`

- Label: R2: D1 EMA20 non-up gate, RR 2.00
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_v2_robustness_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_V2_ROBUSTNESS_202207_202606_XAUUSD_M5_short_v2_r2_d1_ema20_nonup.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_v2_robustness_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_V2_ROBUSTNESS_202207_202606_XAUUSD_M5_short_v2_r2_d1_ema20_nonup_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_v2_robustness_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_V2_ROBUSTNESS_202207_202606_XAUUSD_M5_short_v2_r2_d1_ema20_nonup_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_v2_robustness_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_V2_ROBUSTNESS_202207_202606_XAUUSD_M5_short_v2_r2_d1_ema20_nonup_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_v2_robustness_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_V2_ROBUSTNESS_202207_202606_XAUUSD_M5_short_v2_r2_d1_ema20_nonup_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_v2_robustness_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_V2_ROBUSTNESS_202207_202606_XAUUSD_M5_short_v2_r2_d1_ema20_nonup_summary.json`
- Order activity: `{"rows": 8881, "actions": {"ORDER_SEND_OK": 393, "GUARD_BLOCK": 8488}, "guard_reasons": {"pass": 393, "own_position_exists": 924, "h1_trend_filter_block": 5937, "stop_ceiling_exceeded": 123, "h4_trend_filter_block": 1082, "d1_support_state_gate": 144, "estimated_cost_r_too_high": 277, "spread_too_high": 1}}`

### `short_v2_r3_d1_ema50_structural_down`

- Label: R3: D1 EMA50 structural down gate, RR 2.00
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_v2_robustness_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_V2_ROBUSTNESS_202207_202606_XAUUSD_M5_short_v2_r3_d1_ema50_structural_down.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_v2_robustness_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_V2_ROBUSTNESS_202207_202606_XAUUSD_M5_short_v2_r3_d1_ema50_structural_down_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_v2_robustness_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_V2_ROBUSTNESS_202207_202606_XAUUSD_M5_short_v2_r3_d1_ema50_structural_down_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_v2_robustness_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_V2_ROBUSTNESS_202207_202606_XAUUSD_M5_short_v2_r3_d1_ema50_structural_down_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_v2_robustness_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_V2_ROBUSTNESS_202207_202606_XAUUSD_M5_short_v2_r3_d1_ema50_structural_down_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_v2_robustness_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_V2_ROBUSTNESS_202207_202606_XAUUSD_M5_short_v2_r3_d1_ema50_structural_down_summary.json`
- Order activity: `{"rows": 8881, "actions": {"ORDER_SEND_OK": 242, "GUARD_BLOCK": 8639}, "guard_reasons": {"pass": 242, "own_position_exists": 628, "h1_trend_filter_block": 5937, "stop_ceiling_exceeded": 82, "h4_trend_filter_block": 1082, "d1_support_state_gate": 732, "estimated_cost_r_too_high": 178}}`

## Interpretation

The baseline failed because long-side momentum entries were much worse than shorts. If a variant improves materially, it should be treated as a hypothesis for forward testing, not as a proof of profitability. The cleanest next action is to forward-observe or demo-test only the winning diagnostic variant at minimum size, with the baseline retained as the control.
