# EURUSD executable-sizing frequency portfolio preregistration

Date: 2026-07-30

Status: **FROZEN_BEFORE_SIZING_RESULT**

Demo-order authorization: **false**

## Question

The selected forward-only frequency diagnostic normalized every component to
0.01 lot. That removed the protected portfolio's already broker-tested sizing:
0.02 lot for its profitable chop sleeve and 0.01 lot for compression.

This test restores those unchanged executable volumes while retaining 0.01 lot
for every RSI trade. It does not add, remove, or reselect a trade. The RSI
health gate remains the previously frozen global 30-closed-trade/PF-1.05 rule.

## Frozen admission

The two-year portfolio must retain at least 0.85 trades/weekday and 40%
weekday coverage, full PF at least 1.40, stressed PF at least 1.25,
best-5%-removed PF at least 1.00, PF above 1.15 in both chronological halves,
second-half PF at least 1.25, second-half stressed PF at least 1.10,
second-half best-5%-removed PF at least 1.00, at least 60% positive active
months, closed-trade drawdown no greater than $25, and maximum concurrency no
greater than two.

The extra 0.5-pip stress charge scales with volume. A 0.02-lot protected chop
trade therefore receives twice the dollar stress applied to a 0.01-lot trade.

## Boundary

This is a single predetermined sizing restoration, not a sizing grid. The RSI
gate was mined from the same two-year broker history and failed its earlier
historical transfer. Even a pass can authorize only a disarmed prospective
router build, never demo orders.
