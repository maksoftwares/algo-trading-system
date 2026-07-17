# XAUUSD M30 Chop Dukascopy Portability V1 Preregistration

Date: `2026-07-17`

## Question

Does the unchanged M30 chop range-rotation specialist that was borderline on
Capital.com transfer to a complete ten-year Dukascopy Bid/Ask source and survive
the fixed chronological and cost gates?

## Frozen Ancestry

- Corrected source commit: `50bf9b5d`.
- Family: `CHOP_RANGE_ROTATION_CONTINUATION_V1`.
- Timeframe: M30 aggregated from six contiguous M5 bars.
- Regime: unchanged completed-H4 chop classifier and hysteresis.
- Signal: unchanged prior `1.5` z-score excursion memory, EMA-center crossing,
  two-hour directional confirmation, and directional M30 candle.
- Target: unchanged opposite `1.25` z band.
- Stop: unchanged `1.25` entry ATR.
- Hold: unchanged 12 elapsed hours.
- Cooldown: unchanged six hours by direction.
- Regime exit, market-gap behavior, M5 execution ordering, and stop-first
  ambiguity handling are unchanged.

The five source files and original config are hash-locked in the new config. No
signal, regime, target, stop, hold, or cooldown parameter may change in V1.

## New Data Adapter

- Verified Dukascopy XAUUSD cache: 708,538 M5 rows from 2016-07-01 through
  2026-06-30, SHA-256 locked.
- Entry and exit use native Bid/Ask sides.
- M30 and H4 bars require every constituent M5 bar; no gap filling.
- Stress spread uses the exact M5 bar's maximum tick spread at entry and exit.
- Stress also subtracts `$0.30` per trade, `$0.35` per 24 hours held, and `0.05R`.
- One ounce is used for converting price risk to the fixed ticket costs.

## Chronological Gates

- Train: 2016-07-01 through 2021-06-30.
- Validation: 2021-07-01 through 2024-06-30.
- Exam: 2024-07-01 through 2026-06-30.
- Full: 2016-07-01 through 2026-06-30.

Every period must independently pass its frozen minimum sample, baseline PF,
stressed PF, stressed average R, drawdown, and winner-removal gates. Full history
must have at least 120 trades, baseline PF `1.20`, stressed PF `1.10`, positive
stressed expectancy, at least 60% positive active years, drawdown no greater than
`20R`, and positive stressed net after removing the ten best winners.

The exam must have at least 25 trades, baseline PF `1.20`, stressed PF `1.10`,
and positive stressed expectancy. Failure of any chronological stage rejects V1.

## Boundary

This is a portability test of an already frozen candidate, not a parameter
search. Same-version repair is forbidden. A pass would establish only a
retrospective independent chop specialist candidate; exact MT5 parity,
independent review, and prospective shadow evidence would still be mandatory.
