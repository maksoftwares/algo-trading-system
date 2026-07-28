# EURUSD Neutral prospective operations planner V1.4 preregistration

Date: `2026-07-28`

Status: `FROZEN_BEFORE_PROSPECTIVE_START_AND_FIRST_SIGNAL`

V1.4 adds one forecast-admissibility timing guard to V1.3. In the final
one-to-ten-minute polling tier, a one-minute interval anchored to the previous
capture can fall after the frozen release-minus-60-second forecast deadline.
That could skip the last admissible polling opportunity and later report a
no-trade despite a forecast becoming visible before the deadline.

V1.4 clamps any scheduled pre-release poll to the earlier of:

- the cadence-derived next poll; and
- the exact release-minus-60-second forecast deadline.

At the deadline the poll becomes due. After the deadline, the unchanged base
planner still rejects an event with no captured forecast as
`MISSED_NO_TRADE`; no late backfill is allowed.

V1.4 delegates all other behavior to immutable V1.3. It changes no event
family, forecast value, direction, signal, entry, stop, target, cost,
frequency, ownership, oracle, validation, or broker rule.

At this freeze there are zero actual, event-market, ownership, signal,
terminal-trade, and oracle rows. The cache contains 6,090 hash-validated
symbol-hours with zero safe gaps. No historical P&L was loaded.

V1 through V1.3 remain intact for audit. New operations use
`plan_prospective_neutral_operations_v1_4.py`.
