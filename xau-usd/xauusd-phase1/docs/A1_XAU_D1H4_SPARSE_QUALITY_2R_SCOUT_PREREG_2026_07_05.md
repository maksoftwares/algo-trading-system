# A1 XAU D1/H4 Sparse Quality 2R Scout Prereg - 2026-07-05

Status: `PREREG_DIAGNOSTIC_ONLY`

## Purpose

The latest M5 attempts failed in a consistent way: they could create activity and hold roughly `2R`
payoff, but win rate stayed near `30-33%`. The quiet-day companion test also showed that filling
the current frontier's missing days with those M5 sources restores activity but breaks WR/W-L.

This preregisters a sparse-quality scout instead of another M5 frequency source. It tests completed
D1 context with completed H4 confirmation, looking for high-quality `2R` decisions that might later
compose with the current frontier without diluting its core metrics.

## Boundary

- Offline diagnostic only over broker-exported XAUUSD M5 bars.
- No MT5 terminal launch, chart/profile/preset edit, order, position, or runtime attach.
- No headline/demo claims. A promising frozen exam row would still require exact MT5 Strategy
  Tester implementation/replay in `C:\MT5A1M5MomentumBacktest`.

## Data

- Bar file: `xau-usd/xauusd-phase0/data/processed/bars/capital_com/XAUUSD/M5/XAUUSD_capital_com_M5_20160103_20250701.csv`
- Design window: `2016-01-01 -> 2021-12-31`
- Exam window available to this diagnostic: `2022-07-01 -> 2025-06-30`
- D1 bars use Dubai calendar days and are only available after that day completes.
- H4 confirmation uses completed UTC 4-hour blocks.
- Entry is next M5 bar open after completed H4 confirmation.
- Same-bar TP/SL collisions resolve adverse-first.

## Fixed Families

1. `trend_pullback_resume`: prior D1 trend is up/down, prior D1 was a pullback against trend, and
   completed H4 confirms resumption.
2. `inside_breakout`: prior D1 is inside the previous D1 range, and completed H4 breaks out in the
   trend direction.
3. `outside_reversal`: prior D1 is an outside expansion day, and completed H4 confirms reversal from
   the prior D1 extreme.
4. `range_mid_reclaim`: prior D1 range is large, and completed H4 reclaims the prior D1 midpoint
   from an extreme side.

## Fixed Grid

- Family: `{trend_pullback_resume, inside_breakout, outside_reversal, range_mid_reclaim}`
- Direction: `{long, short}`
- Trend slope minimum: `{0.00, 0.05}`
- H4 body fraction minimum: `{0.20, 0.40}`
- H4 close-location threshold: `{0.60, 0.75}`
- Stop anchor: `{h4, d1}`
- Session filter: `{liquid, no_rollover}`

Total variants: `4 * 2 * 2 * 2 * 2 * 2 * 2 = 256`.

Target is fixed at `2.0R`; stop buffer is fixed at `0.10 * ATR14`; stale exit is fixed at `1440`
M5 bars.

## Selection Rule

Only the design window selects candidates. The top five design rows by the fixed owner-shape score
are frozen into the exam. The report must publish the top design rows and all frozen exam rows,
including failures.

## Promotion Rule

This diagnostic can only justify exact-MT5 implementation if a frozen exam row reaches:

- WR `>=50%`
- W/L `>=2.0`
- active weekdays `>=10%` as a sparse high-quality source
- last-12 WR `>=48%`
- last-12 W/L `>=1.85`

Sparse candidates are not demo-ready by themselves. They can only become components for later
composition if exact MT5 replay and robustness pass. No reviewer token is spent unless a frozen exam
row meets the above diagnostic promotion rule.
