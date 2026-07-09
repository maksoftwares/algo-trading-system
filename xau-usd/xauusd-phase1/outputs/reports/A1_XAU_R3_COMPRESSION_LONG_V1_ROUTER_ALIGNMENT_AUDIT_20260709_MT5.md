# A1 XAU M5 Momentum Continuation Variant Backtests

Generated: `2026-07-09T08:38:10.061163+00:00`
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
| `r3_alignment_full_window_regime_snapshot_m5` | `0` | `0.0%` | `0` | `None` | `0.00 (0.00%)` | `0` | `0` | `fail` |

## Winner Status

- Status: `NO_VARIANT_CLEARS_MINIMUM_BAR`
- Note: Positive diagnostic variants still need forward confirmation before runtime promotion.

## Artifacts

### `r3_alignment_full_window_regime_snapshot_m5`

- Label: Full-window EA-router regime snapshot for R3 trade attribution
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r3_router_alignment_audit_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R3_ROUTER_ALIGNMENT_AUDIT_202207_202606_XAUUSD_M5_r3_alignment_full_window_regime_snapshot_m5.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r3_router_alignment_audit_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R3_ROUTER_ALIGNMENT_AUDIT_202207_202606_XAUUSD_M5_r3_alignment_full_window_regime_snapshot_m5_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r3_router_alignment_audit_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R3_ROUTER_ALIGNMENT_AUDIT_202207_202606_XAUUSD_M5_r3_alignment_full_window_regime_snapshot_m5_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r3_router_alignment_audit_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R3_ROUTER_ALIGNMENT_AUDIT_202207_202606_XAUUSD_M5_r3_alignment_full_window_regime_snapshot_m5_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r3_router_alignment_audit_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R3_ROUTER_ALIGNMENT_AUDIT_202207_202606_XAUUSD_M5_r3_alignment_full_window_regime_snapshot_m5_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r3_router_alignment_audit_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R3_ROUTER_ALIGNMENT_AUDIT_202207_202606_XAUUSD_M5_r3_alignment_full_window_regime_snapshot_m5_summary.json`
- Order activity: `{"rows": 0, "actions": {}, "guard_reasons": {}}`

## Interpretation

The baseline failed because long-side momentum entries were much worse than shorts. If a variant improves materially, it should be treated as a hypothesis for forward testing, not as a proof of profitability. The cleanest next action is to forward-observe or demo-test only the winning diagnostic variant at minimum size, with the baseline retained as the control.
