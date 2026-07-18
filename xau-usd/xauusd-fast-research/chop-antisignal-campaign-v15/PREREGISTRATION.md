# Chop Paired Anti-Signal Campaign V15 Preregistration

## Purpose and provenance

V14 rejected all 1,000 episode-state policies. The rejection was structured:
large groups lost in every era, and several policies with more than 100 executed
trades had worst-era PF below 0.50. V15 therefore tests one explicit hypothesis:
the V14 event definitions contain stable information, but their trade direction
was wrong.

V14 outcomes were exposed before this hypothesis was written. V15 is consequently
a new, outcome-derived historical discovery campaign, not independent evidence.
Its contract hashes the V14 result and metrics as provenance.

## Paired design

- Attempts 30239 through 31238 pair one-for-one with V14 attempts 29239 through
  30238.
- The same 1,000 parameter definitions are retained in the same source order.
- Signal bars, episode features, ancestry, hour windows, and geometries are unchanged.
- Only direction is reversed.
- Entry remains the next M15 executable bid/ask open.
- Stops, locked-R targets, maximum holds, costs, stress slippage, overlap, and daily
  entry limits are unchanged.
- Episode boundaries exclude the current signal bar and all future bars.

## Frozen data

The campaign uses the free verified Dukascopy bid/ask M5 cache from 2016-07-01
through 2026-07-01. M15 bars generate signals and the latest completed H4 bar owns
the regime. No Databento or paid data is used.

## Frozen gates

A finalist needs at least 100 total trades and 15 in every era, total stress PF at
least 1.25, every-era stress PF at least 1.10, every-era average stress R at least
0.02, closed-trade drawdown no more than 25R, and positive net stress R after its
five largest winners are removed. Benjamini-Hochberg correction is applied to all
1,000 daily p-values at FDR 0.10.

## Decision rule

An economic survivor is a historical candidate only. Because V15 was motivated by
V14 outcomes, raw-tick confirmation, an independently frozen replication, and
prospective shadow evidence are mandatory. Failure rejects direction inversion as
a general chop solution. Shock remains an intentional abstain state.
