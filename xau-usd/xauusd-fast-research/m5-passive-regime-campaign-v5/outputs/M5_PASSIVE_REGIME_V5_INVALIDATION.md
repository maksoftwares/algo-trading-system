# XAUUSD M5 Passive Regime Campaign V5 Invalidation

Decision: `INVALIDATED_CLOCK_UNIT_MISMATCH_NO_QUANTITATIVE_INFERENCE`

The locked V5 runner compared M5 bar starts stored as integer milliseconds with
M15 decisions stored as integer microseconds and, inside the simulator,
nanoseconds. Every activation lookup was therefore out of bounds. The run was
stopped before the first 25-policy progress checkpoint, no trade return was
evaluated, and no metrics or result artifact was written.

V5 cannot support any quantitative conclusion. A corrected version must keep the
identical 1,000-definition manifest and normalize all timestamps to UTC
nanoseconds before opening outcomes.

No model training, Python serving, EA, demo, live, or broker authority is granted.
