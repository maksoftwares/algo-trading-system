# A1 XAU M5 Split Break-Distance Guard Exact Probe Preregistration

Date: 2026-07-05

Purpose: exact-MT5 implementation check for the strongest current near miss:
`f33_r30_be_1r + block_ANY_break_distance_atr <= 0.8994`.

Interpretation of the diagnostic gate:
- The internal diagnostic gate blocks rows where `break_distance_atr <= 0.8994`.
- The exact-MT5 implementation therefore uses `InpMinBreakDistanceAtr = 0.8994`.
- The goal is implementation parity and signal-quality evidence, not a demo claim.

Boundary:
- Run only in isolated MT5 Strategy Tester root `C:\MT5A1M5MomentumBacktest`.
- No live/demo chart, order, position, preset, profile, or broker runtime is touched.
- No reviewer token is spent unless the exact run reaches WR >= 50% and realized W/L >= 2.0.

Frozen component set:
- `goal_split_f33_r30_be_1r_v6`, priority 1.
- `goal_split_f33_r30_be_1r_weak`, priority 2.
- `goal_split_f33_r30_be_1r_v13`, priority 3.

Exact MT5 inputs:
- Base component inputs are unchanged.
- Split entry: first lot fraction 1/3, first target 0.70R, runner target 3.00R, runner BE at +1.0R.
- New guard: `InpMinBreakDistanceAtr = 0.8994`.
- `InpMaxBreakDistanceAtr = 0.0`, disabled.

Post-processing:
- Group each component's split tickets by `(entry_time, direction)` and sum ticket P&L to one signal outcome.
- Dedupe same-direction component clusters within four minutes by priority, matching Step 1.
- Report signal-level WR, average win/loss, active-day percentage, manual P&L, drawdown, and last-12-month metrics.

Caveat:
- The threshold was discovered on the same 2022-07-01 through 2026-06-30 window in the internal diagnostic, so even a pass is not demo-ready.
- A pass would justify a robustness package or reviewer question; a fail is discarded.
