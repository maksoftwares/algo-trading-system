# V72 XAG-to-XAU Event-Time Catch-Up Preregistration

Date: `2026-07-20`

## Incremental Hypothesis

Silver and gold share precious-metals information, but silver can update first.
V72 tests a raw-quote mechanism that has not been tested by the earlier H1
relative-value rules or the M15 cross-asset model: after a material XAGUSD move
over 1-20 seconds, trade XAUUSD in the same direction only while the strictly
prior XAU quote has responded by no more than a locked fraction of that move.

V59/V60 are immutable. V72 is an additive research sleeve and cannot alter,
remove, resize, or rescue a V59 trade.

## Causality

- A decision is anchored to an observed XAG quote timestamp.
- The XAG baseline is the last quote at or before the horizon boundary.
- The current XAU quote is strictly earlier than the XAG decision timestamp.
- The prior XAU quote is at or before the horizon boundary.
- All baselines must satisfy the locked staleness limits.
- Entry is the first XAU quote strictly after the decision timestamp.
- ATR comes only from a completed M5 bar.

## Outcome-Blind Calibration

July 2018 is calibration. It may inspect event timestamps, directions, quote
counts, coverage, and candidate density only. It may not create or read an exit,
P/L, MAE, MFE, target result, stop result, future XAU quote, or V59 outcome.

The fixed grid contains exactly `5 x 5 x 5 x 4 x 2 = 1,000` policies:

- horizon: 1, 2, 5, 10, or 20 seconds;
- minimum absolute XAG move: 1, 2, 3, 4, or 5 bps;
- minimum directional innovation: 0.5, 1, 1.5, 2, or 2.5 bps;
- maximum signed XAU response ratio: 0, 0.25, 0.5, or 0.75;
- minimum XAG quote count: 2 or 5.

Select the deterministic policy closest to 0.80 candidates per eligible full
weekday, provided density is 0.65-1.00, active-day share is at least 0.65, and
each direction is at least 20%. Ties choose stricter movement, innovation,
response, and quote-count thresholds, then the shorter horizon.

## Sealed Splits

- Development: 2018-08-01 through 2021-06-30.
- Confirmation: 2021-07-01 through 2022-06-30.
- Validation: 2022-07-01 through 2024-06-30.
- Exam: 2024-07-01 through 2026-06-30.

Each later split remains sealed unless every gate in the prior split passes.
The July 2024-June 2026 XAG source is the final untouched exam source. To avoid
unnecessary network use, it is acquired from the same free official endpoint
only after development, confirmation, and validation all pass. Its manifests,
hour coverage, URLs, and hashes must receive a separate immutable source audit
before the exam runner can open one outcome.

## Execution And Gates

Long entry/exit uses Ask/Bid and short entry/exit uses Bid/Ask. Stop distance is
the maximum of 0.50 completed-M5 ATR, four entry spreads, and USD 1.00. Target is
1.50R and maximum holding time is 15 minutes. Costs include native spread, USD
0.30 per ticket, proportional holding cost, and an extra 0.05R stress charge.

Every split must satisfy its registered minimum sample, 0.65-1.00 trades per
eligible weekday, positive base and stressed net, base PF >=1.30, stressed PF
>=1.20, positive-day share >=45%, positive-month share >=60%, both directions
>=20%, each chronological half stressed PF >=1.05, positive stressed net after
removing the five largest winners, stressed closed DD <=USD 150, and a five-day
circular-block one-sided bootstrap p-value <=0.01.

Failure is terminal for V72. No threshold, direction, exit, cost, quota, split,
or gate may be changed after an outcome is opened.
