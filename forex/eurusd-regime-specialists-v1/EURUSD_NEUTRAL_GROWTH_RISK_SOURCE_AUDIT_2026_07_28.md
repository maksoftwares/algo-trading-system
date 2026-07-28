# EURUSD Neutral Growth/Risk Source Audit

Date: 2026-07-28
Status: source accepted for a new causal research family; no EURUSD outcome was inspected during this audit.

## Result

The prepared growth/risk panel is suitable for an outcome-blind EURUSD Neutral-regime signal census.

- Origin: official Dukascopy Jetta v1 only.
- Cost/access: free, no login, no paid data, no Databento.
- Instruments: `USA500.IDX-USD`, `COPPER.CMD-USD`, and `USD-CNH`.
- Native input: official hourly tick payloads.
- Curated resolution: completed M5 bars.
- Coverage: January 2022 through June 2026.
- Curated rows: 334,801.
- Duplicate M5 timestamps: zero.
- Missing-bar policy: no forward fill when returns are calculated.
- Forbidden content: the curated panel contains no EURUSD outcome, P&L, target-first label, strategy score, or broker action.

## Causal timestamp contract

Every instrument has a source-last timestamp and an availability timestamp. A bar with open timestamp `t` is usable only at `t + 5 minutes`, and its final source tick must be strictly earlier than that availability timestamp.

The 60-minute feature is a log-close difference over 12 M5 bars and is populated only when the source timestamps are exactly contiguous. The research join must be exact—never an as-of join—and every required instrument must have:

1. `available_timestamp_ms == decision_time_ms`;
2. `source_last_timestamp_ms < decision_time_ms`; and
3. a non-null contiguous 60-minute return.

Otherwise the decision is cash.

## Integrity hashes

- Curated parquet SHA-256: `c1b03f03c19af300dc378f892e8d538b7c5a4a05e66e09572de896b1359a16c3`
- Curated manifest SHA-256: `874363b2f866172a01954f538d05063d3ede9ab232b51163d21bfbb281215b28`
- Manifest-recorded curated SHA-256: `c1b03f03c19af300dc378f892e8d538b7c5a4a05e66e09572de896b1359a16c3`

The filesystem hash and manifest-recorded hash agree.

## Outcome-blind capacity preview

The clock review used only Neutral dates, causal feature availability, and the signs of the three external returns. It did not read EURUSD future bars, oracle membership, exits, or P&L.

Three economically distinct UTC handoffs were retained before outcome inspection:

- 03:00: late-Asia handoff;
- 09:00: European morning;
- 15:00: US cash/risk session.

The clocks were chosen for session interpretation and broad source continuity, not for EURUSD performance. The exact candidate census remains gated behind the preregistration hash lock.

## Limitation

These are CFD and spot-FX proxies, not centralized cash-index, futures, or onshore-CNH feeds. The panel can support a causal hypothesis test, but it does not prove that a tradeable EURUSD edge exists. All EURUSD P&L remains locked behind chronological development and confirmation gates.
