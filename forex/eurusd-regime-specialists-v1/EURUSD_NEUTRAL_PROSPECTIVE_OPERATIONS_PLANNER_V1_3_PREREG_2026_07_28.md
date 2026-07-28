# EURUSD Neutral prospective operations planner V1.3 preregistration

Date: `2026-07-28`

Status: `FROZEN_BEFORE_PROSPECTIVE_START_AND_FIRST_SIGNAL`

V1.3 adds one fail-closed dependency gate to V1.2. A future chronological
rehearsal showed that an operator who fell behind could receive both a bounded
cache-prewarm command and an ownership-capture command in the same plan. One
bounded prewarm may not close a large historical gap, so executing both
commands without replanning could bypass the intended bounded acquisition
sequence.

V1.3 requires ownership dates to be processed chronologically. A due event or
oracle-context ownership capture remains blocked until:

1. it is the earliest still-missing required ownership date; and
2. its cache reports zero missing safely completed symbol-hours.

After every mutating command, the planner must be rerun. A later ownership date
cannot become due while an earlier required date remains absent.

V1.3 delegates all event, oracle-context, polling, and command generation to
the immutable V1.2 planner. It changes no strategy or evidence semantics. No
event family, direction, threshold, entry, stop, target, cost, frequency,
validation, oracle, or broker rule changes. Oracle labels remain
evaluation-only.

At this freeze there are zero actual, event-market, ownership, signal,
terminal-trade, and oracle rows. The live cache contains 6,085 hash-validated
symbol-hours and zero safe gaps. No historical P&L was loaded.

V1 through V1.2 remain intact for audit. New operations use
`plan_prospective_neutral_operations_v1_3.py`.
