# Pullback Swing Replication V7 Preregistration

## Selection history

An exposed diagnostic screen evaluated interpretable combinations of action,
mechanism, direction, regime, session, H1/H4 ADX, ATR state, recent directional
movement, spread state, and weekday from 2019-01-01 through 2026-07-01. Sixty-one
unconstrained combinations were positive with PF at least 1.15 in every block.

Before opening any pre-2019 outcome, V7 advances exactly one rule because it had the
highest minimum block PF among practical fixed-action rules and retained positive
top-five-winners-removed P&L after applying one-open-position execution.

## Frozen rule

- Source events: the locked V1 candidate-action ledger.
- Exclude `UNSAFE_SHOCK`.
- Action: exactly `SWING_2R_36H`.
- H1 ADX: `> 20.0` and `<= 30.0`.
- Directional one-hour return: `dir_return_1h_atr <= -0.25`.
- One open V7 position at a time.
- Maximum two accepted V7 entries per UTC date.
- Sort entries by `entry_time`, then `event_id`; an exit at an entry timestamp frees
  capacity before the entry.
- No mechanism, direction, session, weekday, or regime filter may be added.

## Locked replication window

`2016-07-18T00:00:00Z` through `2019-01-01T00:00:00Z`, end exclusive.

This period was not used by the V7 diagnostic selector. It is historical
reverse-time replication, not a claim of an untouched project-wide holdout.

## Replication gates

All gates must pass:

- at least 80 executed trades;
- at least 0.12 trades per weekday;
- stress fixed-lot USD PF at least 1.20;
- positive average and net stress USD;
- closed-trade drawdown no more than USD 120;
- positive net USD after removing the five largest winners;
- at least 60% positive calendar months;
- long and short directions each have at least 25 trades and positive net USD;
- the month-cluster bootstrap 95% lower bound for average USD per trade is above
  zero, using 20,000 resamples and seed `770031`.

## Additive audit

V7 also reports, without promotion authority, the frozen Core plus V7 in the known
confirmation and final windows. Core trades can never be removed, resized, or
replaced. Independent marginal frequency excludes V7 entries within 60 minutes of
a Core entry.

## Decision

Passing all gates yields only
`V7_REVERSE_REPLICATION_PASS_REQUIRES_MT5_PARITY_AND_FORWARD_SHADOW`.
Any failed gate yields `V7_REJECTED`.

No same-version tuning is allowed after the reverse replication result is opened.
No Python prediction, EA, demo, live, or broker action is authorized.
