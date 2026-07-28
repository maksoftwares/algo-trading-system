# EURUSD prospective Neutral ownership preregistration

Date: `2026-07-28`

Status: `FROZEN_BEFORE_PROSPECTIVE_START`

The prospective macro/cross-asset strategy may not accept a manually supplied
Regime 1 label. This producer freezes how each eligible UTC date obtains its
Neutral ownership record from information completed by midnight. It is pinned
to the corrected prospective execution V2.1 contract.

For EURUSD, GBPUSD, USDJPY, the Dukascopy dollar index, and the Dukascopy
Treasury-price CFD, capture the prior 60 calendar days of public hourly tick
files append-only. Aggregate each hour immediately and never forward-fill a
missing hour. Run the unchanged two-clock classifier on the intersection of
the five H1 series.

The decision row is the latest common completed five-market H1 classifier row
no later than the prior date's 23:00 cutoff. This matches the historical
parent's backward-as-of routing rule. No forward-fill or tolerance is used,
and the selected row's staleness from the cutoff is recorded. At least 520
common H1 rows must exist and every terminal EMA, ATR, shock threshold,
range/ATR, and compression threshold must be finite. Otherwise the date
remains cash.

A date belongs to Regime 1 only when:

- classifier direction is `NEUTRAL`;
- shock is false; and
- DXY and EURUSD are not jointly compressed.

The raw payload, request metadata, normalized H1 bars, classifier contract,
terminal feature row, and per-symbol evidence chain are hashed. The record may
be archived after midnight because the public archive has a lag, but it must
exist before any event signal entry. No event reaction, oracle label, trade
outcome, interpolation, alternate lookback, or classifier repair is allowed.

The five public endpoints were probed before this lock and returned HTTP 200
without authentication. This component cannot place broker orders.
