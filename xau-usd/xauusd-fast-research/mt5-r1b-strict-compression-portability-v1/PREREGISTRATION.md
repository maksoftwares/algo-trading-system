# MT5 R1B Strict Compression Uptrend Dukascopy Portability V1

Date: `2026-07-17`

## Question

Does the fixed MT5 `r1_long_expansion_r3_reclass_strict_r1` rule retain positive
after-cost expectancy on Dukascopy, and is its opportunity set sufficiently distinct
from the two-day R1 rule to count as another specialist?

## Fixed Rule

The regime owner, shock veto, completed-bar rules, 2R execution, Bid/Ask handling,
cost stress, and two-position/one-entry-per-day primary policy are identical to the
R1 portability study. The signal definition is fixed to the MT5 preset:

- Prior D1 box: three completed days.
- D1 ATR(14) percentile over 252 bars: at or below 60.
- One third of box width: at most 1.25 times median D1 range(20).
- Completed H4 bullish breakout body: at least 35% of range.
- Stop: max(H4 close minus box low, H4 ATR(14), $3.50); target: 2R.

The primary policy must pass every chronological economic gate. It must then have
same-direction entry overlap within 60 minutes at or below 20% of the smaller trade
set and absolute daily stress-P&L correlation at or below 0.60 versus R1. Economic
survival without independence is not a second specialist.

Stages are 2017-07 through 2021-06, 2021-07 through 2024-06, and 2024-07 through
2026-06. No retrospective period is described as untouched.

Research only. No model training, EA consumption, demo order, or live order is
authorized.
