# COMEX-Spot Receipt Innovation V70 Preregistration

## Purpose And Information Boundary

V70 is a research-only attempt to add 0.65-1.00 qualified trades per full
weekday without changing any V59/V60 trade, risk rule, or result. Existing
COMEX-versus-spot work used completed M5 bars. V70 tests a different causal
input: the event-time price innovation visible when an exchange trade reaches
Databento, compared with the latest raw Dukascopy quote strictly before that
receipt decision.

No clock shift, timestamp optimization, future quote, paid request, model,
Python signal service, EA, demo/live action, or broker action is permitted. The
historical periods have informed other research; even an all-stage pass is only
a near-survivor requiring unchanged prospective shadow evidence.

V69 froze the same mechanism but stopped before writing any development
candidate, label, audit, or economic result. It incorrectly asserted that the
Databento receive clock could never precede the publisher event clock.
Databento defines `ts_recv` as the primary sort/index timestamp and documents
that publisher clocks may be unsynchronized. V70 removes only that invalid
cross-clock assertion, records the affected-row count, and repeats calibration
under a new contract. No strategy threshold, grid, execution rule, or gate is
changed.

## Fixed Mechanism

COMEX trades are ordered solely by `ts_recv` and aggregated into completed 100 ms
receipt buckets. A decision occurs at the bucket end, strictly after every
source trade used. For each registered horizon, V70 calculates:

- the COMEX price move from the last received price at or before the horizon
  boundary to the last received price in the completed bucket;
- signed and total COMEX volume received inside the horizon;
- the Dukascopy executable-mid move between quotes strictly before the same two
  boundaries; and
- directional innovation: COMEX-move sign times COMEX move minus spot move.

Both spot quotes must be no more than 1,000 ms stale and the COMEX baseline no
more than 500 ms stale. COMEX move, signed-flow direction, and innovation must
agree. V70 follows the COMEX direction. The earliest qualifying event per UTC
date is retained; there is no daily quota fill or replacement.

## Outcome-Blind Calibration

Calibration is 2022-07-01 through 2022-08-01. It may expose only source quality,
feature counts, candidate counts, candidates per eligible full weekday,
active-day share, and direction balance. Post-decision prices, entries, exits,
returns, MFE, MAE, P/L, win rate, and profit factor are prohibited.

Exactly 1,000 deterministic policies are registered:

- horizon: 250, 500, 1,000, 2,000, or 5,000 ms;
- minimum absolute COMEX move: USD 0.40, 0.60, 0.80, 1.00, or 1.20;
- minimum directional innovation: USD 0.20, 0.30, 0.40, 0.50, or 0.60;
- minimum absolute signed-volume imbalance: 0.00, 0.15, 0.30, or 0.45; and
- minimum received contracts: 5 or 10.

A policy is selectable only at 0.65-1.00 candidates per eligible full weekday,
at least 65% active days, and at least 20% each direction. Selection minimizes
distance from 0.80/day and then prefers stricter move, innovation, imbalance,
and volume thresholds, followed by the shorter horizon. No economic outcome
participates. If none qualifies, V70 ends before contract lock.

## Frozen Economic Geometry

- Session: 08:20 inclusive to 13:30 exclusive, America/New_York.
- Entry: first verified Dukascopy quote strictly after the decision and within
  1,000 ms.
- Long enters at ask and exits at bid; short enters at bid and exits at ask.
- Stop: max(0.25 completed-M5 ATR, four entry spreads, USD 0.50).
- Target: 1.00R; timeout: two minutes; one XAU ounce research size.
- Ticket cost: USD 0.30; prorated holding cost: USD 0.35 per 24 hours.
- Stress: an additional adverse 0.05R per resolved trade.

Chronological stages open separately: development 2022-08-01 to 2024-07-01,
validation 2024-07-01 to 2025-07-01, and exam 2025-07-01 to 2026-07-01.

Each stage requires the locked 0.65-1.00/day density; positive base/stress net
and mean; base PF >= 1.20; stress PF >= 1.10; at least 40% profitable full days;
at least 60% positive months; at least 20% each direction; both half-stage
stress PF values >= 1.00; positive stress net after removing five winners;
closed stress drawdown <= USD 150; and a centered-null five-weekday circular
block-bootstrap one-sided p-value <= 0.01. Development requires 300 resolved
trades; validation and exam require 150 each.

No same-version threshold, direction, horizon, timestamp, session, stop,
target, hold, cost, or gate rescue is authorized after outcomes open.
