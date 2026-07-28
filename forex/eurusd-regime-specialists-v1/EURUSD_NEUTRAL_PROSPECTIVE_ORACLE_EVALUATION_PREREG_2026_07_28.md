# EURUSD Neutral prospective oracle evaluation preregistration

Date: `2026-07-28`

Status: `FROZEN_BEFORE_PROSPECTIVE_START_AND_FIRST_SIGNAL`

This component measures whether the frozen causal strategy resembles the
Regime 1 hindsight oracle. It is evaluation-only. Oracle rows may never enter
signal generation, evidence selection, trade routing, risk, sizing, or exits.

The authoritative historical full-calendar oracle evaluates every existing
EURUSD M5 entry on a UTC weekday, scans up to 12 hours of later bid/ask bars,
and selects the first four target-before-stop winners. It tries a fixed 4-pip
risk first and a fixed 3-pip fallback only if 4 pips cannot produce four
winners. Target, cost, tie-break, and stop-first rules remain exactly frozen.

## Safe known time

The last possible candidate of a date begins at 23:55 UTC and its 12-hour
outcome horizon ends at 11:55 UTC the next day. Therefore a complete daily
oracle is not admissible until the next day at 12:01 UTC:

- oracle date start plus 36 hours;
- plus a 60-second public-archive capture lag;
- and no earlier than the observed time of the required next-day five-market
  context evidence.

The next day's frozen ownership capture supplies the completed context through
the oracle date. Regime assignment uses the historical backward-as-of rule:
latest common five-market H1 state no later than entry hour minus one hour.
Only rows assigned `NEUTRAL` are eligible for the imitation-precision match.

All raw EURUSD payloads, request metadata, completed bid/ask M5 bars, ownership
context, oracle rows, and manifests are immutable and hashed. Missing intervals
are preserved. If the exact frozen rules cannot find four winners, the date is
persisted as complete but oracle-unavailable; no threshold or risk repair is
allowed.

The first valid oracle date is `2026-07-29`. Existing history remains
development data and cannot be imported into this prospective ledger. This
component makes no broker request and grants no trading authorization.
