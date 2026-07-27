# V6 Causal ML Early Exit Cross-Asset V5 Preregistration

## Hypothesis

V4's XAUUSD-only path features cannot reliably separate temporary adverse
movement from continued failure. Broad dollar and Treasury movement available
at the decision time may improve that distinction.

## Frozen V4 Policy

- Frozen V1 selected nominations and broad causal training corpus.
- Frozen V3 XAUUSD path features and checkpoints at 30, 60, 120, and 240
  minutes.
- Frozen V4 unclipped target:
  `(early stressed P&L - frozen stressed P&L) / initial risk`.
- Frozen V4 25th-percentile histogram gradient-boosting regressor and equal
  total weight per UTC decision day.
- Frozen V4 action threshold and adverse-state guards.
- Frozen annual target years, 48-hour purge, windows, costs, routing, and all
  economic and risk gates.

## Only Authorized Change

Add these features:

- DXY log return over 1 hour and 4 hours.
- US Treasury total-return index log return over 1 hour and 4 hours.
- One-hour common-dollar factor:
  `(-EURUSD return - GBPUSD return + USDJPY return) / 3`.
- Availability flags for every return.
- Current-source staleness in minutes for DXY, Treasury, and the maximum of the
  three FX components.

At decision time `T`, a source bar timestamped `S` is usable only when
`S + 5 minutes <= T`. Both endpoints of each return must be available and no
more than 10 minutes older than their intended completed-bar cutoff. No
forward fill is allowed across a closure. An unavailable return is zero and
its availability feature is zero.

Transitive text dependency locks require exact bytes or, solely when the exact
hash differs, the expected hash after replacing CRLF with LF. This
line-ending-only fallback is recorded in the contract. Binary files have no
fallback.

## Source Coverage Gates

Across frozen V1 target snapshots, availability must be at least:

- 80% for DXY 1-hour returns.
- 80% for Treasury 1-hour returns.
- 80% for the common-dollar 1-hour factor.

## Decision

V5 passes only if all frozen V4 model, annual, economic, window, account-risk,
and drawdown gates pass, the source coverage gates pass, and the V4 dependency
hashes remain unchanged.

All inspected history is development evidence. Same-version tuning is
forbidden. A failed V5 is quarantined. A passing V5 remains research-only and
requires a separately locked prospective period and MT5 parity before any
execution discussion.
