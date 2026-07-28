# EURUSD prospective Neutral ownership cache prewarm preregistration

Date: `2026-07-28`

Status: `FROZEN_BEFORE_PROSPECTIVE_START_AND_FIRST_OWNERSHIP_RECORD`

The frozen prospective ownership producer needs 7,200 public hourly payloads
for its first date: 60 calendar days, 24 hours per day, and five markets. Its
correct sequential fallback is too large to leave as a cold-start operation
on the first eligible date. This helper populates the producer's exact
append-only raw and metadata cache ahead of time.

The helper cannot classify a date, create an ownership record, generate a
signal, inspect an oracle or outcome, calculate P&L, or contact a broker. It
only requests hours inside the already frozen ownership window whose H1 bar
has been complete for at least 60 seconds.

## Compatibility contract

Every new response must:

- identify the requested frozen symbol and UTC hour;
- have an evidence observation time after that hour completed;
- decode with the unchanged cumulative-delta implementation;
- aggregate as one valid H1 bar or a preserved empty market hour;
- be written under the exact raw and metadata paths already consumed by the
  ownership producer; and
- remain immutable under SHA-256.

The primary producer still validates every cached hash, rebuilds all H1 bars,
runs the unchanged five-market classifier, and creates the only authoritative
ownership record. Prewarming grants no ownership and changes no strategy rule.

## Bounded transport

The cache may be populated in deterministic batches of no more than 720 new
requests, using at most eight workers. A request receives at most three
attempts with fixed one- and three-second retry delays. Failed batches retain
already validated immutable payloads and can resume without overwriting them.

The first target date is `2026-07-29`. At most 7,200 symbol-hours are required;
hours not yet safely complete remain pending rather than being requested.
