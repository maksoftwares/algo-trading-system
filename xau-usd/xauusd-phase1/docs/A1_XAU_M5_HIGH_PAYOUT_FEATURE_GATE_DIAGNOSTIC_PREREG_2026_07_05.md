# A1 XAU M5 High-Payout Feature-Gate Diagnostic Preregistration

Generated: 2026-07-05

## Purpose

The Step 3 owner-goal portfolio composition pass found two opposing shapes:

- the best frequent portfolio reached 4,128 exact-MT5 signals, 50.02% WR, and 86.58% active weekdays, but only 1.3227 realized average win / average loss;
- the high-payout frontier reached 3,500-4,400 exact-MT5 signals and 2.5+ realized average win / average loss, but only about 36% WR.

This diagnostic tests whether measurable MT5 signal features can block enough low-quality trades from the high-payout frontier to approach the owner shape without inventing exits, prices, or trades.

## Boundary

- Offline diagnostic only.
- Inputs are exact MT5 Strategy Tester trade CSVs, exact MT5 signal ledgers, and adjacent MT5 signal-log CSVs.
- No MT5 launch, no runtime attach, no charts, no presets, no orders, and no broker state mutation.
- Python may join realized trade rows to the MT5 signal logs by `(source_csv, entry_time, direction)` and recalculate realized metrics after hypothetical entry blocking.
- The result is not a headline claim. Any surviving filter must be rerun in exact MT5 before review or forward-demo discussion.

## Fixed Base Portfolios

The base portfolios are fixed from the Step 3 high-payout frontier before this diagnostic runs:

1. `hp_core_orrev_simple`: `step1_f33_r30_be_never` + `orrev_london_firm_stop10`.
2. `hp_core_v13_orrev`: `step1_f33_r30_be_never` + `v13_ema_trend_h1h4_both_rr2p0_no_weak_short_no_long_morning` + `orrev_london_firm_stop10`.
3. `hp_core_v13_v9_orrev`: `step1_f33_r30_be_never` + `v13_ema_trend_h1h4_both_rr2p0_no_weak_short_no_long_morning` + `v9_sweep_h1h4_long_rr2p0_v4mask` + `orrev_london_firm_stop10`.

These were chosen because they are active, high-payout exact-MT5 portfolios, not because they already satisfy the owner gate.

## Candidate Feature Rules

The diagnostic may test one single feature block at a time, optionally direction-specific:

- `spread_points`
- `atr`
- `body_fraction`
- `close_location`
- `three_bar_move_atr`
- `break_distance_atr`
- `estimated_cost_r`
- `signal_range`
- `recent_range`
- `close_to_recent_extreme`
- `against_wick_points`
- `against_wick_body_ratio`

Thresholds are taken only from coarse quantiles: 10%, 15%, 20%, 25%, 30%, 70%, 75%, 80%, 85%, and 90%. This is a triage scan, not a final specification.

## Decision Rules

- `OWNER_DIAGNOSTIC_HIT`: WR >= 50%, realized avg win/loss >= 2.0, active weekday coverage >= 90%, positive net, retention >= 50%.
- `CORE_SHAPE_REPLAY_CANDIDATE`: WR >= 50%, realized avg win/loss >= 2.0, active weekday coverage >= 50%, positive net, retention >= 50%.
- `NEAR_OWNER_REPLAY_CANDIDATE`: WR >= 47.5%, realized avg win/loss >= 2.0, active weekday coverage >= 50%, PF >= 1.40, positive net, retention >= 50%.
- Otherwise reject.

Reviewer spend is preserved unless an exact-MT5 replay validates a candidate. This offline diagnostic alone is not review-worthy.
