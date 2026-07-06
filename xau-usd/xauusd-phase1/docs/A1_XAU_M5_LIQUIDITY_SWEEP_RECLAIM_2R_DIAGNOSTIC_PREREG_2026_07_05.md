# A1 XAU M5 Liquidity Sweep Reclaim 2R Diagnostic Prereg - 2026-07-05

Status: `PREREG_DIAGNOSTIC_ONLY`

## Purpose

The current exact-ledger hybrid frontier can preserve the owner's core shape only around
`50.23%` win rate, `2.0002` realized average win/loss, and `86.39%` active weekdays. Attempts to
buy activity from the existing F67/V7/V11 pool push win rate below `50%`.

This preregisters one genuinely different M5 source: a liquidity sweep and reclaim pattern. It is
intended to test whether false breaks of recent highs/lows can produce a high-win-rate, 2R-native
activity source suitable for later exact-MT5 implementation.

## Boundary

- This run is **offline diagnostic only** over broker-exported M5 bars.
- It does not launch MT5, attach to runtime terminals, touch charts, presets, orders, or positions.
- It cannot produce headline/demo claims. A promising row would require a frozen EA implementation
  and exact MT5 Strategy Tester replay in `C:\MT5A1M5MomentumBacktest`.

## Data

- Bar file: `xau-usd/xauusd-phase0/data/processed/bars/capital_com/XAUUSD/M5/XAUUSD_capital_com_M5_20160103_20250701.csv`
- Design window: `2016-01-01 -> 2021-12-31`
- Exam window available to this diagnostic: `2022-07-01 -> 2025-06-30`
- Entry prices use ask open for longs and bid open for shorts.
- Exit/stop checks use bid prices for long exits and ask prices for short exits.
- Same-bar TP/SL collisions resolve adverse-first.

## Signal Definition

All decisions use only completed bars.

For a short signal:

1. A completed M5 bar's high sweeps above the selected reference high by at least
   `sweep_min_atr * ATR14`.
2. The same completed bar closes back below the reference high by at least
   `close_back_atr * ATR14`.
3. The entry is the next M5 bar open.
4. The stop is beyond the sweep bar high by `stop_buffer_atr * ATR14`.
5. The target is `2.0R`.
6. If neither stop nor target is reached after `288` M5 bars, the position exits at the then-current
   close. This is fixed, not optimized.

Long signals mirror the same logic around the selected reference low.

One position is allowed at a time inside this diagnostic; signals while a position is open are
skipped.

If a single completed bar triggers both long and short sweep-reclaim conditions, the bar is skipped
as ambiguous.

## Fixed Grid

The full design ledger will include every combination:

- Reference: `{rolling_48, rolling_96, previous_dubai_day, asia_range}`
- Direction mode: `{both, long, short}`
- Sweep minimum ATR: `{0.05, 0.15, 0.30}`
- Close-back ATR: `{0.00, 0.05}`
- Stop buffer ATR: `{0.05, 0.15}`
- Trend filter: `{none, range}`
- Session filter: `{liquid, no_rollover}`

Total variants: `4 * 3 * 3 * 2 * 2 * 2 * 2 = 576`.

## Selection Rule

Only the design window selects candidates. The top five design rows by the fixed owner-shape score
are frozen into the exam:

`score = WR_core + WL_core + active_core + PF_core + sample_core`

where each component is capped and monotonic toward the owner goal. The report must publish the
top design rows and all five exam rows, including failures.

## Promotion Rule

This diagnostic can only justify an exact-MT5 replay candidate if an exam row reaches:

- signal-level win rate `>= 50%`
- realized average win/loss `>= 2.0`
- active weekdays `>= 70%` as a standalone source, or a clear low-overlap activity role
- last-12-months win rate `>= 48%` and realized average win/loss `>= 1.85`

If no exam row clears those thresholds, the family is rejected or parked as a weak clue. No reviewer
token is spent.
