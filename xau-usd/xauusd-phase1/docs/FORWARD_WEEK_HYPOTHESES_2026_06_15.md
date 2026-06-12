# Forward Week Hypotheses - 2026-06-15

Status: `PRE_REGISTERED_PENDING_WEEK`

Registration boundary: this file must be committed before the Monday 2026-06-15 trading week starts. The commit hash is the lock. Do not edit these hypotheses after the week starts; supersede with a new dated file if needed.

Scope: experimental demo evidence only. This does not approve canonical Phase 2, live trading, or real capital.

## H1 - Round-Family Night/Evening Shorts

Hypothesis: round-family SHORT signals during Dubai Night `20:00-05:59` and Evening `16:00-19:59` are net-positive after cost in the fresh week.

H1 evidence floor: broker-joined-only unless `OBSERVER_REPLAY_CALIBRATION_REPORT.md` reaches `PASS_REPLAY_USABLE` or `WARN_REPLAY_USABLE_WITH_ERROR_BAR`; quarantined replay is descriptive only.

Pass metric:

- Use duplicate-hidden family-level rows only.
- Include `symbol_normalized_round_retest_v0` and `round_number_retest_v0` as one `round` family.
- Evaluate only closed broker-joined rows, plus replay rows only if replay calibration is `PASS_REPLAY_USABLE` or better.
- PASS if family-level net R after cost is `> 0.00R` and closed win rate is above the cell `net_breakeven_wr_pct`.

Fail metric:

- FAIL if net R after cost is `<= 0.00R`, or if the cell needs replay evidence while replay calibration remains `< 75%`.

## H2 - M15/H1 Trend Veto

Hypothesis: the M15/H1 trend veto improves weak-lane net expectancy without damaging control-lane signal coverage.

Pass metric:

- Weak lanes: `symbol_normalized_round_retest_v0`, `round_number_retest_v0`, `session_extreme_retest_v0`, and repair variants.
- Control lanes: `breakout_retest` and `swing_breakout_retest_v0`.
- PASS if veto-BLOCK rows have worse realized or calibrated net R than veto-KEEP rows, and control-lane KEEP coverage remains `>= 60%`.

Fail metric:

- FAIL if veto-BLOCK rows are not worse than veto-KEEP rows, or if control-lane KEEP coverage falls below `60%`.

## H3 - Family Mutex

Hypothesis: after a family duplicate mutex is applied, duplicate rate drops to approximately zero and portfolio unique-view PF is at least `1.20`.

Pass metric:

- Duplicate rate target: `<= 2%` duplicate rows in actual broker CSV.
- Max same-symbol/same-direction same-family stack: `<= 2`.
- Portfolio unique-view PF target: `>= 1.20`.

Fail metric:

- FAIL if duplicate rate remains `> 2%`, max stack is `> 2`, or unique-view PF is `< 1.20`.

## H4 - Breakout-Retest Control Stability

Hypothesis: `breakout_retest` control remains day-positive on the majority of active demo days.

Pass metric:

- Evaluate `breakout_retest` only.
- Use duplicate-hidden broker-joined actual trades.
- PASS if positive-PnL days are greater than negative-PnL days across the fresh week.

Fail metric:

- FAIL if positive-PnL days are equal to or fewer than negative-PnL days, or if sample size is fewer than `3` active days.

## Evidence Rules

- Broker-joined outcomes outrank replay outcomes.
- Replay-only rows are decision-eligible only if `OBSERVER_REPLAY_CALIBRATION_REPORT.md` is at least `WARN_REPLAY_USABLE_WITH_ERROR_BAR`; if it is `FAIL_REPLAY_QUARANTINED`, replay-only rows are descriptive only.
- Portfolio totals must use family-level de-duplicated rows.
- Runtime changes from Block A require owner authorization and a before/after maintenance-window report.
