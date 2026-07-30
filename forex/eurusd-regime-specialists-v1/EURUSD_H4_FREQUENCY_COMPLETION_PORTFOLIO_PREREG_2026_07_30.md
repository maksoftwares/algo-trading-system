# EURUSD H4 frequency-completion portfolio preregistration

This exact portfolio is frozen before its combined outcome is calculated.
It is adaptive historical research, not a pristine holdout, and it cannot
authorize broker orders.

## Frozen construction

- Preserve all 1,288 trades from the passing H4 confirmation portfolio.
- Add the exact M30 first-break family already locked by the intrahour
  frequency ladder.
- Add only the four fixed M15 follow-through horizons that passed the
  predeclared standalone rule: chop at +3 and +5 bars, and compression at +5
  and +7 bars after the first qualified overnight-range break.
- Give each M15 follow-through trade 0.25 initial risk units. Preserve the
  locked M30 family's 2:1 chop/compression weighting at 0.25R/0.125R.
- Apply a 2.5R causal candidate cap with the fixed priority in the JSON
  contract.
- After trade admission, apply one uniform scale to every accepted trade. The
  scale is the minimum needed to keep maximum concurrent risk at or below
  1.5R and closed-trade drawdown at or below 17.5R. This scale cannot change a
  trade timestamp, side, order, or admission.

The full raw family has a theoretical capacity near one trade per FX day
before overlap and the causal risk cap.

## Required backtest outcome

The exact combined ledger must achieve at least 0.85 trades per FX day, PF
1.15, PF 1.10 after another 0.5 pip, PF 1.00 after another 1.0 pip, PF above
1 in every chronological block, recent and latest-12-month PF 1.20, positive
latest-six-month R, 45%-55% wins, 1.35-1.75 realized payoff, at least 55%
positive active months, best-5%-removed PF 1.00, drawdown no greater than
18R, and passing trade-block and calendar-block bootstrap tails.

Each added component must retain its standalone qualification. The smallest
final 0.1-lot-equivalent sleeve size must remain at least the broker's
0.01-lot minimum.

Failure rejects this exact construction. No losing year, regime, session, or
expert may be removed after seeing the combined result.

## Pre-outcome correction

The first implementation run stopped before portfolio assembly because the
M30 family had mistakenly been transcribed with equal regime weights. This
document and its lock were updated before any combined outcome was calculated
to preserve the already locked M30 2:1 chop/compression weighting. The
standalone concentration gate remains unchanged.
