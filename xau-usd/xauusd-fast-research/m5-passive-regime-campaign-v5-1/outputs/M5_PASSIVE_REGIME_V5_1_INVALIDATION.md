# XAUUSD M5 Passive Regime Campaign V5.1 Invalidation

Decision: `INVALIDATED_UNBOUNDED_MEMOIZATION_NO_QUANTITATIVE_INFERENCE`

The corrected clock passed all audits, but the run's memoization cache grew
without a bound across the 1,000-policy campaign. At the last reported checkpoint
it had processed 125 policies, held 846,283 cached outcomes, and used 2.49 GB of
private memory while the machine had 11.1 GB of free physical memory. The linear
projection was unsafe, so the process was stopped before resource exhaustion.

No metrics, rankings, shortlist, or result artifact was written or inspected.
V5.1 therefore supports no quantitative conclusion. A streaming correction must
keep the byte-identical manifest and all trading rules unchanged, bound cache life
to fixed policy blocks, and prove cached versus uncached result parity.

No model training, Python serving, EA, demo, live, or broker authority is granted.
