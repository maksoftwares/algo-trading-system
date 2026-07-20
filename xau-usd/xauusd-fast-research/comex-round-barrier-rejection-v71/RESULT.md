# COMEX Round-Barrier Rejection V71 Result

Date: 2026-07-20
Decision: `V71_DEVELOPMENT_FAIL_TERMINAL`
Authority: historical research only

V71 registered exactly 1,000 round-price rejection policies and selected one
using only July 2022 candidate density, active-day coverage, and direction
balance. Its immutable rule used USD 10 barriers, a 120-second lookback, a USD
0.40 probe, a USD 0.80 rejection, and at least 0.25 opposite five-second flow.

Development resolved 383 trades over 491 eligible full weekdays, or 0.780041
trades per weekday, with 203 longs and 180 shorts. Density and direction balance
held, but every economic and stability requirement failed:

- base net: USD -238.78;
- stress net: USD -268.00;
- base PF: 0.5118;
- stress PF: 0.4733;
- profitable-day share: 25.66%;
- positive-month share: 13.04%;
- first/second-half stress PF: 0.4298 / 0.5208;
- stress net after removing five winners: USD -284.24;
- closed stress drawdown: USD 282.92; and
- one-sided block-bootstrap p-value: 1.0.

Validation and exam remain sealed. The fixed round-barrier rejection family is
terminal and cannot be rescued with a different spacing, window, threshold,
direction, breakout mirror, session, exit, cost, or quota on these outcomes.

Contract SHA-256:
`5d22a4a05669f5be0eb3a1d4618387e7431c3a75f20eeb56425d20071ba7e263`

Development audit SHA-256:
`f7fdcf5bdb9df9c6be308418f1e2c2f8d534d747b84dad4f16ed60d77a67f9b0`
