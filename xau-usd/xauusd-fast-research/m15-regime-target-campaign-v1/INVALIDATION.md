# M15 Regime Target Campaign V1 Invalidation

Status: `INVALIDATED_NO_QUANTITATIVE_INFERENCE`

V1 completed its locked run, but every definition reported zero selected trades. A post-run execution audit found a timestamp-unit defect in `execution_arrays`:

- `timestamp_utc` was converted to integer microseconds;
- `bar_start_utc` was converted to integer milliseconds;
- `simulate_trade` interpreted both arrays as nanoseconds.

For the first eligible candidate, the completed signal and next bar both represented `2010-01-19T10:00:00Z`, but the raw integers were `1263895200000000` and `1263895200000`. The calculated entry gap was therefore `-21043.85508` minutes, and every candidate was rejected.

The recorded V1 metrics and result remain unchanged for auditability. They do not provide evidence for or against any chop or transition definition.

A new pre-outcome V2 contract must normalize every timestamp array to nanoseconds and include a mixed-resolution regression test before rerunning the unchanged definitions under new attempt numbers.
