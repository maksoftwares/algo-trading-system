# Chop Weekly Partial-Rotation V13 Preregistration

## Decision question

Can partial rotation toward causal weekly anchors produce an economically robust
XAUUSD specialist while the frozen H4 owner regime is `CHOP`?

V12 found that London wick rotations toward the weekly open had positive stressed
results but only 47 full-anchor trades and one trade in the weakest era. V13 is an
explicit historical follow-up. It freezes a target at 25%, 50%, or 75% of the
signal-to-anchor distance so more rotations can complete without loosening entry or
risk gates. `UNSAFE_SHOCK` is never eligible.

## Data and causality

Only the free verified Dukascopy bid/ask M5 foundation from 2016-07-01 through
2026-07-01 is used. M15 signals use a regime attached from the latest completed H4
bar. Weekly open is known from the first completed bar of the week. Weekly VWAP is
cumulative through the signal bar. Prior-week high, low, and midpoint are shifted by
one completed UTC week. Return and rejection features use completed bars only.

Entry is the next complete M15 opening quote. Stops and partial targets use the
executable bid or ask side. If both are touched in one bar, the stop wins. Costs and
stress slippage are deducted. No anchor or target moves after entry.

## Locked search

Exactly 1,000 definitions, attempts 28239 through 29238:

- 200 weekly-open partial rotations.
- 200 cumulative-week-VWAP partial rotations.
- 200 prior-week-midpoint partial rotations.
- 200 prior-week-edge reentries.
- 200 London weekly-impulse fades.

Manifest membership is determined before outcomes by SHA-256 ordering and minimum
signal coverage only. It cannot use forward returns, trade outcomes, PF, or P&L.
All 1,000 rows are included in false-discovery adjustment.

## Economic gates

- At least 100 trades and 15 trades in every era.
- Stress PF at least 1.10 and average stress R at least 0.02 in every era.
- Total stress PF at least 1.25.
- Closed-trade drawdown no more than 25 R.
- Positive net after removing the five largest winners.

Any historical survivor requires separately locked raw-tick replay, independent
replication, and prospective shadow evidence. No result authorizes training or
execution.
