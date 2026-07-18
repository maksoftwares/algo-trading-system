# Chop Microstructure Anti-Signal V17 Preregistration

## Purpose and provenance

V16 tested 1,000 native M5 microstructure policies inside causal H4 chop and found
no survivor. High-sample flow-continuation definitions lost consistently after
costs, commonly near PF 0.60 across eras. V17 tests one explicit hypothesis: the
events are informative but immediate M5 flow direction should be faded.

V16 outcomes were exposed before V17. This is an outcome-derived historical
discovery campaign, not independent evidence. Its contract hashes V16 result and
metrics.

## Paired design

- Attempts 32239 through 33238 pair one-for-one with V16 attempts 31239 through
  32238.
- All 1,000 parameter definitions retain source order, signal timestamps, causal
  H4 chop labels, episode ages, sessions, and raw signal counts.
- Stops, targets, maximum holds, contiguous next-M5 entry, bid/ask execution,
  costs, stress slippage, overlap, cooldown, and daily limits are unchanged.
- Only trade direction is reversed.

## Frozen data and gates

The source is the free verified Dukascopy M5 bid/ask and tick-derived feature cache
from 2016-07-01 through 2026-07-01. No paid data or Databento data is used.

A finalist needs at least 100 trades and 15 in every era, total stress PF at least
1.25, every-era stress PF at least 1.10, every-era average stress R at least 0.02,
closed drawdown no more than 25R, and positive net stress R after removing its five
largest winners. Benjamini-Hochberg correction applies across all 1,000 policies at
FDR 0.10.

## Decision rule

Any survivor remains a historical candidate only and requires independently frozen
replication plus prospective shadow evidence. Failure rejects generic M5
microstructure direction inversion inside chop. Shock remains an abstain state.
