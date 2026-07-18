# Chop Exit-Hazard Antisignal V19 Preregistration

## Purpose and exposed history

V18 tested 1,000 completed-H4 CHOP exit-pressure policies and found no economic
finalist. Many sufficiently sampled direct policies lost materially after costs.
V19 tests one narrow follow-up: the same pressure may identify failed breaks that
should be faded rather than followed.

V18 outcomes are exposed. V19 therefore permits no new signal, threshold, session,
episode-age, or geometry search. It is an exact paired direction inversion.

## Exact pairing

- Attempts 34239 through 35238 pair one-to-one with V18 attempts 33239 through
  34238.
- Signal timestamps, raw counts, parameters, sessions, CHOP ownership, state age,
  and H1-ATR geometry are identical to the paired V18 row.
- V18 `LONG` becomes V19 `SHORT`; V18 `SHORT` becomes V19 `LONG`.
- The preflight compares every parameter JSON and signal count to the frozen V18
  manifest and fails on any mismatch.

## Frozen data and execution

The source remains the free verified Dukascopy bid/ask M5 cache from 2016-07-01
through 2026-07-01. State features use only completed H4/H1 bars. Entry remains the
next contiguous side-correct M5 open. The four H1-ATR stop/target/hold geometries,
spread cap, ticket cost, holding cost, 0.05R stress slippage, stop-first collision
rule, cooldown, and daily cap are unchanged from V18.

## Frozen gates

A finalist needs at least 100 trades and 15 in every era, total stress PF at least
1.25, every-era stress PF at least 1.10, every-era average stress R at least 0.02,
closed drawdown no more than 25R, and positive net stress R after removing its five
largest winners. Benjamini-Hochberg correction applies across all 1,000 policies at
FDR 0.10.

## Decision rule

Any survivor is historical discovery evidence only. It must pass separately locked
implementation parity, independent confirmation, and prospective shadow testing.
Failure rejects this exact failed-break direction inversion without weakening gates.
Shock remains an intentional abstain state.
