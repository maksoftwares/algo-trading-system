# Transition Online Component Router V10 Post-Run Invalidation

## Decision

`INVALID_IMPLEMENTATION_DO_NOT_INTERPRET_POLICY_OUTCOMES`

V10 completed 1,000 manifest rows, but none of those rows is a valid strategy
attempt. The screen must not be used as evidence for or against online routing.

## Root cause

The V9 parquet stores `entry_time` and `exit_time` as `datetime64[ms, UTC]`.
`build_shadow_cache` converted the exit series with `astype("int64")`, producing
milliseconds since epoch, but converted each entry with `Timestamp.value`, producing
nanoseconds since epoch. Every history-window search therefore returned an empty
slice.

Post-run diagnostic:

- Cache records: 1,756.
- Maximum shadow count: 0.
- Nonzero shadow records: 0.
- Distinct `(trade count, PF)` outcome pairs across 1,000 rows: 2.

The only observed behaviors were cold-start `BASE`, `HALF`, or `OFF`; no declared
trailing statistic was actually evaluated.

## Corrective action

V10 remains immutable. V11 will normalize both entry and exit timestamps to
nanoseconds explicitly, add a real-precision regression test, allocate a new attempt
range, and seal a new contract before outcomes are opened.
