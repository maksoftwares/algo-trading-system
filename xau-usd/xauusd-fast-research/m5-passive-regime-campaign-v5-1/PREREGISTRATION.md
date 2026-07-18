# XAUUSD M5 Passive Regime Campaign V5.1 Preregistration

V5 was invalidated before quantitative outcomes because M5 bar starts were
compared as millisecond integers against microsecond and nanosecond M15 decision
integers. V5.1 is a clock-only correction.

The mechanics, parameter values, deterministic sample, attempt numbers 21,120
through 22,119, order semantics, execution stress, era windows, economic gates,
and FDR policy are unchanged. The V5.1 manifest must be byte-identical to V5 and
retain SHA-256 `938891405dc64b22b5e11378405c2bcf8d8af71df8839471f4febede0fc1595a`.

Before any outcome is opened, V5.1 must prove that:

1. Millisecond, microsecond, and nanosecond UTC inputs normalize to the same
   nanosecond epoch.
2. Every M5 end is after its start.
3. M15 activation lookups have no negative gap.
4. The first contiguous M5 activation after a completed M15 decision has zero
   gap when the source bars are contiguous.
5. The conservative pending-limit quote-side and fill-bar rules from V5 remain
   unchanged.

Historical outcomes remain discovery evidence. A finalist requires separate
exact-tick confirmation and prospective shadow observation. No model training,
Python serving, EA, demo, live, broker, network, Databento, or paid-data authority
is granted.
