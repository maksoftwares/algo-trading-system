# EURUSD Neutral specialist-agreement census preregistration

Date: `2026-07-29`

Status: `FROZEN_BEFORE_SIGNAL_CENSUS`

The trailing-P&L allocator failed. This distinct lane tests contemporaneous
causal agreement instead: at an exact entry timestamp, at least two of the
unchanged eight mechanism-diverse specialists must signal the same side. Any
opposing specialist forces cash. Duplicate rows from one expert count once,
and only the earliest valid agreement on a UTC date may be routed.

This first stage is source-bound to `entry_time_utc` and `side`. The CSV reader
is forbidden to load exits, R, prices, target hits, oracle membership, or P&L.
The expert set is identical to the locked online aggregation audit and cannot
be pruned after the census.

Capacity, window coverage, side balance, expert-combination diversity, and
contributor gates are frozen in
`config/frozen_neutral_specialist_agreement_census.json`. Failure closes the
exact agreement rule without opening outcomes. Passing permits only a second
freeze of a canonical four-pip stop, six-pip target execution before EURUSD
prices or outcomes are loaded.

Because component summaries were previously inspected, any eventual historical
result remains a retrospective causal audit and cannot authorize demo or broker
trading without a separate prospective freeze.
