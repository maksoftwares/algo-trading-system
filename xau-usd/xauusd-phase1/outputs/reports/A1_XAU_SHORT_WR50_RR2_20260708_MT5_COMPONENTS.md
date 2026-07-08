# A1 XAU M5 Momentum Continuation Variant Backtests

Generated: `2026-07-07T22:25:19.138126+00:00`
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
| `wr50_s1_m5_sweep_structural` | `84` | `34.52%` | `14.03` | `1.05` | `83.45 (7.75%)` | `14.03` | `0` | `diagnostic_only` |
| `wr50_s2_prior_day_sweep_structural` | `30` | `33.33%` | `-17.08` | `0.88` | `84.21 (8.11%)` | `-17.08` | `0` | `fail` |
| `wr50_s3_ema_pullback_structural` | `377` | `31.83%` | `-80.06` | `0.95` | `290.67 (27.46%)` | `-80.06` | `0` | `fail` |
| `wr50_s4_m5_ema_trend_structural` | `253` | `33.99%` | `9.46` | `1.01` | `293.19 (27.60%)` | `9.46` | `0` | `diagnostic_only` |
| `wr50_s5_v2_strict_retest_structural` | `209` | `34.45%` | `235.05` | `1.31` | `123.22 (11.72%)` | `235.05` | `0` | `diagnostic_only` |

## Winner Status

- Status: `DIAGNOSTIC_WINNER_NOT_PROMOTED`
- Note: This is a backtest-window diagnostic. Do not promote without fresh forward evidence.

## Artifacts

### `wr50_s1_m5_sweep_structural`

- Label: WR50 S1: M5 local high sweep/reclaim, D1 structural down, H1/H4 down
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_WR50_RR2_202207_202606_XAUUSD_M5_wr50_s1_m5_sweep_structural.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_WR50_RR2_202207_202606_XAUUSD_M5_wr50_s1_m5_sweep_structural_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_WR50_RR2_202207_202606_XAUUSD_M5_wr50_s1_m5_sweep_structural_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_WR50_RR2_202207_202606_XAUUSD_M5_wr50_s1_m5_sweep_structural_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_WR50_RR2_202207_202606_XAUUSD_M5_wr50_s1_m5_sweep_structural_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_WR50_RR2_202207_202606_XAUUSD_M5_wr50_s1_m5_sweep_structural_summary.json`
- Order activity: `{"rows": 2791, "actions": {"ORDER_SEND_OK": 84, "GUARD_BLOCK": 2707}, "guard_reasons": {"pass": 84, "h1_trend_filter_block": 1113, "direction_mode_block": 1329, "own_position_exists": 19, "h4_trend_filter_block": 132, "d1_support_state_gate": 94, "estimated_cost_r_too_high": 18, "stop_ceiling_exceeded": 2}}`

### `wr50_s2_prior_day_sweep_structural`

- Label: WR50 S2: prior-day-high sweep/reclaim, D1 structural down, H1/H4 down
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_WR50_RR2_202207_202606_XAUUSD_M5_wr50_s2_prior_day_sweep_structural.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_WR50_RR2_202207_202606_XAUUSD_M5_wr50_s2_prior_day_sweep_structural_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_WR50_RR2_202207_202606_XAUUSD_M5_wr50_s2_prior_day_sweep_structural_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_WR50_RR2_202207_202606_XAUUSD_M5_wr50_s2_prior_day_sweep_structural_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_WR50_RR2_202207_202606_XAUUSD_M5_wr50_s2_prior_day_sweep_structural_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_WR50_RR2_202207_202606_XAUUSD_M5_wr50_s2_prior_day_sweep_structural_summary.json`
- Order activity: `{"rows": 6125, "actions": {"GUARD_BLOCK": 6095, "ORDER_SEND_OK": 30}, "guard_reasons": {"h1_trend_filter_block": 5636, "pass": 30, "own_position_exists": 95, "h4_trend_filter_block": 251, "d1_support_state_gate": 97, "estimated_cost_r_too_high": 15, "stop_ceiling_exceeded": 1}}`

### `wr50_s3_ema_pullback_structural`

- Label: WR50 S3: M5 EMA pullback short, D1 structural down, H1/H4 down
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_WR50_RR2_202207_202606_XAUUSD_M5_wr50_s3_ema_pullback_structural.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_WR50_RR2_202207_202606_XAUUSD_M5_wr50_s3_ema_pullback_structural_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_WR50_RR2_202207_202606_XAUUSD_M5_wr50_s3_ema_pullback_structural_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_WR50_RR2_202207_202606_XAUUSD_M5_wr50_s3_ema_pullback_structural_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_WR50_RR2_202207_202606_XAUUSD_M5_wr50_s3_ema_pullback_structural_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_WR50_RR2_202207_202606_XAUUSD_M5_wr50_s3_ema_pullback_structural_summary.json`
- Order activity: `{"rows": 32257, "actions": {"ORDER_SEND_OK": 377, "GUARD_BLOCK": 31880}, "guard_reasons": {"pass": 377, "direction_mode_block": 16446, "own_position_exists": 1049, "h1_trend_filter_block": 11367, "estimated_cost_r_too_high": 198, "h4_trend_filter_block": 1691, "d1_support_state_gate": 1079, "stop_ceiling_exceeded": 50}}`

### `wr50_s4_m5_ema_trend_structural`

- Label: WR50 S4: M5 EMA trend short, D1 structural down, H1/H4 down
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_WR50_RR2_202207_202606_XAUUSD_M5_wr50_s4_m5_ema_trend_structural.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_WR50_RR2_202207_202606_XAUUSD_M5_wr50_s4_m5_ema_trend_structural_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_WR50_RR2_202207_202606_XAUUSD_M5_wr50_s4_m5_ema_trend_structural_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_WR50_RR2_202207_202606_XAUUSD_M5_wr50_s4_m5_ema_trend_structural_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_WR50_RR2_202207_202606_XAUUSD_M5_wr50_s4_m5_ema_trend_structural_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_WR50_RR2_202207_202606_XAUUSD_M5_wr50_s4_m5_ema_trend_structural_summary.json`
- Order activity: `{"rows": 11113, "actions": {"ORDER_SEND_OK": 253, "GUARD_BLOCK": 10860}, "guard_reasons": {"pass": 253, "own_position_exists": 368, "direction_mode_block": 5916, "h1_trend_filter_block": 3292, "h4_trend_filter_block": 689, "d1_support_state_gate": 482, "estimated_cost_r_too_high": 85, "stop_ceiling_exceeded": 28}}`

### `wr50_s5_v2_strict_retest_structural`

- Label: WR50 S5: stricter V2 breakdown-retest, D1 structural down, H1/H4 down
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_WR50_RR2_202207_202606_XAUUSD_M5_wr50_s5_v2_strict_retest_structural.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_WR50_RR2_202207_202606_XAUUSD_M5_wr50_s5_v2_strict_retest_structural_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_WR50_RR2_202207_202606_XAUUSD_M5_wr50_s5_v2_strict_retest_structural_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_WR50_RR2_202207_202606_XAUUSD_M5_wr50_s5_v2_strict_retest_structural_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_WR50_RR2_202207_202606_XAUUSD_M5_wr50_s5_v2_strict_retest_structural_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_wr50_rr2_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_WR50_RR2_202207_202606_XAUUSD_M5_wr50_s5_v2_strict_retest_structural_summary.json`
- Order activity: `{"rows": 5320, "actions": {"ORDER_SEND_OK": 209, "GUARD_BLOCK": 5111}, "guard_reasons": {"pass": 209, "own_position_exists": 359, "h1_trend_filter_block": 3515, "h4_trend_filter_block": 651, "d1_support_state_gate": 448, "estimated_cost_r_too_high": 94, "stop_ceiling_exceeded": 44}}`

## Interpretation

The baseline failed because long-side momentum entries were much worse than shorts. If a variant improves materially, it should be treated as a hypothesis for forward testing, not as a proof of profitability. The cleanest next action is to forward-observe or demo-test only the winning diagnostic variant at minimum size, with the baseline retained as the control.
