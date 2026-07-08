# A1 XAU M5 Momentum Continuation Variant Backtests

Generated: `2026-07-08T06:42:46.986389+00:00`
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
| `short_htf_resistance_sweep_reclaim_rr2` | `299` | `29.43%` | `-255.11` | `0.84` | `556.24 (48.20%)` | `-255.11` | `0` | `fail` |

## Winner Status

- Status: `NO_VARIANT_CLEARS_MINIMUM_BAR`
- Note: Positive diagnostic variants still need forward confirmation before runtime promotion.

## Artifacts

### `short_htf_resistance_sweep_reclaim_rr2`

- Label: Final WR50/RR2 falsification: M15 reclaim of HTF resistance sweep
- MT5 report: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_htf_resistance_sweep_final_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_HTF_RESISTANCE_SWEEP_FINAL_202207_202606_XAUUSD_M5_short_htf_resistance_sweep_reclaim_rr2.htm`
- Trade CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_htf_resistance_sweep_final_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_HTF_RESISTANCE_SWEEP_FINAL_202207_202606_XAUUSD_M5_short_htf_resistance_sweep_reclaim_rr2_trades.csv`
- Order CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_htf_resistance_sweep_final_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_HTF_RESISTANCE_SWEEP_FINAL_202207_202606_XAUUSD_M5_short_htf_resistance_sweep_reclaim_rr2_orders.csv`
- Signal CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_htf_resistance_sweep_final_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_HTF_RESISTANCE_SWEEP_FINAL_202207_202606_XAUUSD_M5_short_htf_resistance_sweep_reclaim_rr2_signals.csv`
- Management CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_htf_resistance_sweep_final_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_HTF_RESISTANCE_SWEEP_FINAL_202207_202606_XAUUSD_M5_short_htf_resistance_sweep_reclaim_rr2_management.csv`
- Summary JSON: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_short_htf_resistance_sweep_final_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_SHORT_HTF_RESISTANCE_SWEEP_FINAL_202207_202606_XAUUSD_M5_short_htf_resistance_sweep_reclaim_rr2_summary.json`
- Order activity: `{"rows": 2459, "actions": {"ORDER_SEND_OK": 299, "GUARD_BLOCK": 2160}, "guard_reasons": {"pass": 299, "own_position_exists": 446, "d1_support_state_gate": 1563, "stop_ceiling_exceeded": 98, "estimated_cost_r_too_high": 48, "spread_too_high": 5}}`

## Interpretation

The baseline failed because long-side momentum entries were much worse than shorts. If a variant improves materially, it should be treated as a hypothesis for forward testing, not as a proof of profitability. The cleanest next action is to forward-observe or demo-test only the winning diagnostic variant at minimum size, with the baseline retained as the control.
