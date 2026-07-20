# Capital Core Causal Outcome Resolver V40 Preregistration

## Purpose

V28, V29, and V34 emit frozen R1-R4 Capital candidate facts but intentionally
do not create prospective outcomes. V40 closes only that engineering gap. It
does not alter a signal, discover a parameter, summarize aggregate profit,
train a model, or authorize an order.

## Frozen sources

- Forward boundary: `2026-07-20T00:00:00Z`.
- V28 owns the frozen R2/R3 component clocks and fixed-horizon execution.
- V29 owns the frozen R1 pullback clock produced by the exact MT5 EA rules.
- V34 owns the frozen R4 chop clock and its three-component priority stream.
- Every source contract SHA-256 and rule-dependency SHA-256 is fixed in the V40
  configuration. A changed byte fails closed.
- Source JSONL and resolution JSONL bytes already consumed form immutable
  prefixes. Truncation or mutation fails closed.

## Causal execution

V28 uses the first quote at or after the scheduled H4 entry within ten minutes,
an executable stop at `stop_atr * signal_atr`, and the first executable quote at
or after the fixed horizon. Its four-trade daily cap and one-position policy are
applied separately to each component. Composite routing is deliberately left to
the separately locked same-period portfolio evaluator.

V29 uses the first quote at or after the decision time within one minute. The
stop distance is the frozen candidate `stop_points * 0.01`; the target is 2R.
There is no invented time exit. An accepted position remains pending until the
quote ledger observes its stop or target. The exact historical maximum of eight
concurrent positions and twelve entries per UTC day is enforced.

V34 uses the first quote within five minutes, its frozen 1 ATR stop, locked 2R
target, and 12-hour horizon. It applies one shared position, five-minute
post-exit cooldown, component priority, and maximum four entries per UTC day.

Long entries use ask and long exits use bid; short entries use bid and short
exits use ask. Stops pay the first observed executable crossing price. Targets
fill at the locked target on the first crossing. Every final label records the
causal knowledge time and a digest of its supporting Capital quote slice.

## Evidence boundary

V40 may append individual `EXECUTED` and `REJECTED` labels. It may expose counts
and pending reasons, but it may not calculate aggregate P/L, optimize a rule, or
admit a sleeve. Validation and confirmation each require 20 complete weekdays
under a separately locked shared-account evaluator.

## Authority

V40 imports no MT5 package and calls no broker API. It writes only local
append-only outcome ledgers, prefix states, and runtime status. Model training,
Python prediction, EA consumption, demo trading, live trading, and broker action
remain false.
