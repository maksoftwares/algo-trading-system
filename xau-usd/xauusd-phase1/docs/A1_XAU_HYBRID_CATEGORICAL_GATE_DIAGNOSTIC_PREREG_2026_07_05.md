# A1 XAU Hybrid Categorical Gate Diagnostic Preregistration

Generated UTC: `2026-07-05`

## Purpose

Test whether the best broad exact-ledger hybrid can be repaired with simple causal categorical gates before spending more exact MT5 runs or reviewer budget.

## Boundary

- Source evidence: existing exact MT5 Strategy Tester trade/signal CSVs only.
- No MT5 launch.
- No live/demo runtime attach.
- No broker state changes.
- This is diagnostic only. Any hit must be converted into an exact MT5 implementation/replay before reviewer or demo discussion.

## Fixed Baselines

1. `broad_rank4`: `freq_step3_frontier + hp_v13_orrev + split_high_payout_f33_r30_be_never + h4_d1_long_best_box2_atr80 + h4_d1_long_broad_box3_atr60`
2. `wr_rank16`: `freq_step3_frontier + split_high_payout_f33_r30_be_never + h4_d1_long_best_box2_atr80 + h4_d1_long_broad_box3_atr60`

## Fixed Gate Families

The search may block at most two gates from these causal categories:

- entire component
- direction
- server hour
- weekday
- component + direction
- component + hour
- component + weekday
- family group + hour
- direction + hour

No PnL, future, drawdown, or outcome-derived field is allowed as a gate input.

## Decision Rules

- `DIAGNOSTIC_OWNER_SHAPE_HIT`: WR >= 50%, W/L >= 2.0, active weekdays >= 90%, PF >= 1.30, net > 0.
- `DIAGNOSTIC_CORE_NEAR_ACTIVITY`: WR >= 50%, W/L >= 2.0, active weekdays >= 85%, PF >= 1.30, net > 0.
- `DIAGNOSTIC_NEAR_FRONTIER`: WR >= 50%, W/L >= 1.90, active weekdays >= 85%, PF >= 1.30, net > 0.
- Otherwise reject the categorical-gate repair direction for now.

Minimum retained signals for any candidate row: `3000`.
