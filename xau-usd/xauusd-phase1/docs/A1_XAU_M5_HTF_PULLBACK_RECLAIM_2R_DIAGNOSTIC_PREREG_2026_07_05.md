# A1 XAU M5 HTF Pullback Reclaim 2R Diagnostic Prereg - 2026-07-05

Status: `PREREG_DIAGNOSTIC_ONLY`

## Purpose

The latest liquidity sweep-reclaim source proved that raw false-break activity can reach near-daily
coverage and preserve a `2R` realized payoff, but its exam win rate was only about `30%`. This
diagnostic moves the other way: only allow M5 pullback/reclaim entries when a completed
higher-timeframe proxy trend state is already favorable.

The goal is not to create another raw frequency stream. The goal is to test whether a quality-first
intraday continuation source can approach signal-level WR `>=50%`, realized W/L `>=2.0`, and enough
standalone activity to be useful in the owner-goal portfolio.

## Boundary

- Offline diagnostic only over broker-exported XAUUSD M5 bars.
- No MT5 terminal launch, chart/profile/preset edit, order, position, or runtime attach.
- No headline/demo claims. A promising frozen exam row would still require exact MT5 Strategy Tester
  implementation in `C:\MT5A1M5MomentumBacktest`.

## Data

- Bar file: `xau-usd/xauusd-phase0/data/processed/bars/capital_com/XAUUSD/M5/XAUUSD_capital_com_M5_20160103_20250701.csv`
- Design window: `2016-01-01 -> 2021-12-31`
- Exam window available to this diagnostic: `2022-07-01 -> 2025-06-30`
- Entry is next M5 bar open after a completed signal bar.
- Long entry/exit prices use ask open for entry and bid prices for exits; shorts mirror this.
- Same-bar TP/SL collisions resolve adverse-first.

## Signal Definition

All features are derived from completed M5 bars only. The "HTF" state is a causal proxy:
`EMA50` vs `EMA200`, plus EMA50 slope over either `96` M5 bars (about H4) or `288` M5 bars
(about D1), normalized by ATR14.

For a long signal:

1. `EMA50 > EMA200`.
2. `EMA50_slope_window / ATR14 >= slope_min_atr`.
3. Signal bar pulls back to the selected EMA reference (`EMA20` or `EMA50`) within fixed tolerance
   `0.05 * ATR14`.
4. Signal bar closes back above the selected EMA reference by at least `0.02 * ATR14`.
5. Body fraction and close-location thresholds pass.
6. Entry is next M5 bar ask open.
7. Stop is below the recent swing low over the selected stop lookback by `stop_buffer_atr * ATR14`.
8. Target is `2.0R`.
9. If neither target nor stop is reached after `288` M5 bars, exit at then-current close.

Short signals mirror the same logic below EMA references. Long and short variants are evaluated as
separate rows; there is no hidden direction mixing.

One position is allowed at a time in each diagnostic row. Signals while a position is open are
skipped.

## Fixed Grid

- Direction: `{long, short}`
- EMA reference: `{ema20, ema50}`
- Trend slope window: `{96, 288}`
- Slope minimum ATR: `{0.05, 0.12}`
- Minimum body fraction: `{0.25, 0.45}`
- Close-location threshold: `{0.60, 0.75}`
- Stop lookback bars: `{3, 6}`
- Stop buffer ATR: `{0.10}`
- Session filter: `{liquid, no_rollover}`

Total variants: `2 * 2 * 2 * 2 * 2 * 2 * 2 * 1 * 2 = 256`.

## Selection Rule

Only the design window selects candidates. The top five design rows by fixed owner-shape score are
frozen into the exam:

`score = WR_core + WL_core + activity_core + PF_core + sample_core`

The report must publish the top design rows and all five frozen exam rows.

## Promotion Rule

This diagnostic can only justify exact-MT5 implementation if a frozen exam row reaches:

- signal-level win rate `>=50%`
- realized average win/loss `>=2.0`
- active weekdays `>=70%` as a standalone source, or a clear low-overlap activity role
- last-12-months win rate `>=48%`
- last-12-months realized average win/loss `>=1.85`

If no exam row clears those thresholds, the branch is rejected or parked as a weak clue. No reviewer
token is spent.
