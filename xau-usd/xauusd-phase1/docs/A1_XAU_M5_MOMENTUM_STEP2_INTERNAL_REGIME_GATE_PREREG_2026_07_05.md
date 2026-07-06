# A1 XAU M5 Momentum Step 2 Internal Regime Gate Pre-Registration

Generated UTC: `2026-07-05T08:19:31Z`

## Objective

Step 1 split-shape grid is complete with no survivor. Step 2 tests whether a causal, broker-derived market-state gate can improve the completed Step 1 signal books toward the owner goal:

- Signal-level win rate `>=50%`
- Realized average winner / average loser `>=2.0`
- Daily activity reported honestly; `90%+` active weekdays remains the owner activity target, but Step 2 filters are expected to reduce activity and therefore cannot be promoted on their own if activity remains low.

## Boundary

This is offline analysis over exact MT5 Strategy Tester artifacts only:

- Kept signal ledger: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_STEP1_SPLIT_SHAPE_GRID_KEPT_SIGNALS_2026_07_05.csv`
- MT5 `*_signals.csv` files beside the Step 1 trade CSVs
- No live/demo runtime terminal, chart, preset, order, position, or broker-action state may be touched.

## Candidate Cells

The screen is restricted to these Step 1 cells:

| Cell | Reason |
| --- | --- |
| `f33_r30_be_1r` | Best above-`50%` WR payoff point from Step 1 |
| `f33_r30_be_never` | Best W/L and net from Step 1 |
| `f33_r25_be_never` | Clears `2.0x` W/L with less WR damage than `r30` no-BE |
| `f50_r25_be_never` | Half-split no-BE clears `2.0x` W/L |
| `f67_r25_be_never` | Best late two-thirds no-BE compromise |
| `f67_r30_be_never` | Final two-thirds no-BE payoff point |

## Causal Features

Only features present at the MT5 decision bar are allowed:

- `spread_points`
- `atr`
- `body_fraction`
- `close_location`
- `directional_close_location`
- `three_bar_move_atr`
- `abs_three_bar_move_atr`
- `directional_three_bar_move_atr`
- `break_distance_atr`
- `estimated_cost_r`
- `signal_range`
- `recent_range`
- `recent_range_atr`
- `close_to_recent_extreme`
- `against_wick_points`
- `against_wick_body_ratio`
- `server_hour`

The join key is `(variant/source signal CSV, entry_time, direction)` against `WOULD_SIGNAL` rows. There is no future data in these fields.

## Gate Search

The screen is deliberately small:

1. Baseline metrics for each candidate cell.
2. Single block gates:
   - direction scope: `ANY`, `LONG`, `SHORT`
   - operation: block rows where feature `<= threshold` or `>= threshold`
   - thresholds: in-sample feature quantiles `10/15/20/25/30/70/75/80/85/90`
3. Limited two-gate combinations:
   - only top five single gates per cell by predeclared score
   - union of the two block conditions
   - no duplicate feature+direction+operator pair

No gate may be treated as a survivor from this report. A gate that reaches WR/WL targets is only an in-sample clue and must be implemented in MT5, rerun exactly, split-tested, stress-tested, and reviewed before any forward spec.

## Decision Labels

| Label | Meaning |
| --- | --- |
| `IN_SAMPLE_WR_WL_HIT_ACTIVITY_FAIL` | WR `>=50%` and W/L `>=2.0`, but active days `<90%`; Step 3 portfolio or new family still required |
| `IN_SAMPLE_NEAR_WR_WL` | WR `>=49%` and W/L `>=1.8` |
| `FAIL_WR_WL` | Does not meet the signal-level WR/WL target |
| `FAIL_SAMPLE` | Fewer than `700` signals |
| `FAIL_ACTIVITY_MINIMUM` | Fewer than `300` active weekdays |

## Review Policy

Do not spend the reviewer on this screen unless it creates a genuine in-sample WR/WL hit or exposes a methodological decision that must be challenged. If no hit appears, continue to the next family search without review.
