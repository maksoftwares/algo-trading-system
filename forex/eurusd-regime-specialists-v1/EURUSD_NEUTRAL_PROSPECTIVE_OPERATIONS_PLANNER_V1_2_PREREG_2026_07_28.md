# EURUSD Neutral prospective operations planner V1.2 preregistration

Date: `2026-07-28`

Status: `FROZEN_BEFORE_PROSPECTIVE_START_AND_FIRST_SIGNAL`

V1.2 supersedes the runtime-corrected V1.1 planner after an outcome-blind
oracle-lineage audit found a missing operations stage. The frozen oracle
evaluator requires the ownership context captured for the day after each
oracle date. V1.1 scheduled ownership only for target event dates. Therefore
an August 7 NFP signal and an August 13 PPI signal could close causally but
their August 8 and August 14 oracle contexts would never be scheduled.

V1.2 preserves the V1.1 offline `uv` launcher and the unchanged V1 planning
engine. It adds only:

- one required ownership date for each target event date plus one day;
- de-duplication when that date is itself another target event date;
- cache prewarming against the earliest still-missing event or oracle-context
  ownership date; and
- ordering that places a due cache action before a due ownership capture.

For the currently frozen August watchlist, the unique required ownership dates
are August 7, 8, 12, 13, and 14. August 13 is shared by CPI oracle context and
PPI event ownership.

No oracle label is available or used at this freeze. Oracle data remains
evaluation-only and cannot change signal generation, selection, routing,
risk, sizing, or exits. No strategy parameter, event family, entry, stop,
target, cost, frequency policy, validation threshold, or broker boundary is
changed.

At this freeze there are zero actual, event-market, ownership, signal,
terminal-trade, and oracle rows. The ownership prewarm cache contains 6,085
hash-validated symbol-hours with zero safe gaps, and no historical P&L was
loaded.

V1 and V1.1 remain intact for audit. New operations use
`plan_prospective_neutral_operations_v1_2.py`.
