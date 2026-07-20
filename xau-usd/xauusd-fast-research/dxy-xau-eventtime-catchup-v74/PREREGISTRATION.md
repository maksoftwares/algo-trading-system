# V74 DXY-to-XAU Event-Time Catch-Up Preregistration

Date: `2026-07-20`

## New Causal Hypothesis

Earlier macro studies used completed M5/H1 aggregate state. V74 tests a distinct
event-time mechanism: a sharp raw Dollar Index quote move over 1-20 seconds while
the strictly prior XAU quote has not completed the expected inverse response.
The first qualifying event per eligible UTC date becomes a candidate.

At a DXY event timestamp, the DXY baseline and XAU horizon baseline are the last
quotes at or before the horizon boundary. The current XAU quote must be strictly
earlier than the DXY event. Entry is the first XAU quote strictly later than the
event. Expected XAU direction is exactly the inverse of DXY direction.

## Outcome-Blind Calibration

January 2019 may inspect only source coverage, event features, directions, and
candidate density. Exactly 1,000 policies are registered:

- horizon: 1, 2, 5, 10, or 20 seconds;
- minimum absolute DXY move: 0.2, 0.4, 0.6, 0.8, or 1.0 bps;
- minimum inverse-direction innovation: 0.1, 0.2, 0.3, 0.4, or 0.5 bps;
- maximum signed XAU response ratio: 0, 0.25, 0.5, or 0.75;
- minimum DXY quote count: 2 or 5.

The deterministic selection target is 0.80 candidates per eligible weekday,
within 0.65-1.00, active-day share >=65%, and each direction >=20%. Ties choose
stricter move, innovation, response, and quote-count rules, then shorter horizon.

## Chronological Stages

- Development: 2019-02-01 through 2022-06-30.
- Confirmation: 2022-07-01 through 2023-06-30.
- Validation: 2023-07-01 through 2024-06-30.
- Exam: 2024-07-01 through 2026-06-30.

Later stages remain sealed until every prior gate passes unchanged.

## Execution And Gates

Use first-later XAU quote, native bid/ask, completed-M5 ATR, stop at max(0.50 ATR,
four spreads, USD 1.00), 1.50R target, 15-minute timeout, USD 0.30 ticket cost,
proportional holding cost, and 0.05R stress slippage.

Each stage requires its registered sample and 0.65-1.00 trades/weekday, positive
base and stress net, base PF >=1.30, stress PF >=1.20, positive days >=45%,
positive months >=60%, each direction >=20%, each chronological half stress PF
>=1.05, positive stress net after five largest winners are removed, stressed DD
<=USD 150, and five-day block-bootstrap one-sided p <=0.01.

Failure is terminal. No post-outcome direction, threshold, horizon, response,
quota, exit, cost, or gate change is permitted. V59/V60 remain immutable.

