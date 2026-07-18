# XAUUSD M5 Passive Regime Campaign V5.2 Preregistration

V5.1 corrected the clock but was interrupted before result creation because its
memoization cache grew without a bound across all 1,000 policies. No metrics or
rankings were inspected. V5.2 is a resource-only correction.

The V5 manifest, mechanics, signals, pending-order semantics, fills, exits,
costs, attempt numbers, era windows, gates, and statistical policy remain
byte-for-byte or behaviorally unchanged. The only permitted change is clearing
memoized outcomes before each fixed block of 25 policies. Memoization affects
computation reuse only; it cannot affect a recomputed outcome.

Before outcomes are opened, tests must prove:

1. The manifest remains byte-identical with SHA-256
   `938891405dc64b22b5e11378405c2bcf8d8af71df8839471f4febede0fc1595a`.
2. Persistent-cache and block-cleared evaluation produce identical policy
   outputs.
3. A 25-policy block cache clears at the exact registered boundaries.
4. V5.1 nanosecond clock tests still pass unchanged.

Historical outcomes are discovery evidence. A finalist still requires exact-tick
confirmation and prospective shadow observation. No model training, Python
serving, EA, demo, live, broker, network, Databento, or paid-data authority is
granted.
