# V73 Fixed XAG-to-XAU Event-Time Anti-Signal Preregistration

Date: `2026-07-20`

## Hypothesis And Fixed Change

V72's same-direction XAG-to-XAU catch-up rule lost in every development month,
in both directions, and in both chronological halves. V73 asks one question:
does the same extreme one-second silver dislocation identify transient
liquidity noise for which XAU movement in the opposite direction has positive
expectancy?

V73 inherits V72 policy `H01000__XM040__IN025__RR050__QC05` exactly:

- one-second horizon;
- minimum 4.0 bps XAG move;
- minimum 2.5 bps directional innovation;
- maximum 0.50 signed XAU response ratio;
- minimum five XAG quotes;
- first candidate per eligible UTC date.

The only signal change is `LONG -> SHORT` and `SHORT -> LONG`. No threshold,
horizon, event time, quota, session, stop, target, hold, cost, or economic gate
is selected from the exposed V72 result.

## Fresh Chronological Firewall

- V72 exposed period: 2018-08-01 through 2021-06-30.
- V73 development: 2021-07-01 through 2022-06-30.
- V73 confirmation: 2022-07-01 through 2023-06-30.
- V73 validation: 2023-07-01 through 2024-06-30.
- V73 exam: 2024-07-01 through 2026-06-30.

Each later stage remains sealed unless every gate in the preceding stage passes.
The free official XAG exam archive is acquired and audited only after validation
passes, before any exam outcome can be opened.

## Execution And Gates

Execution is exactly V72: native bid/ask, first later quote, completed-M5 ATR,
stop at max(0.50 ATR, four spreads, USD 1.00), 1.50R target, 15-minute timeout,
USD 0.30 ticket cost, proportional holding cost, and 0.05R stress slippage.

Every stage requires at least 150 resolved trades (300 in the two-year exam),
0.65-1.00 trades per eligible weekday, positive base and stress net, base PF
>=1.30, stress PF >=1.20, positive-day share >=45%, positive-month share >=60%,
both directions >=20%, each chronological half stress PF >=1.05, positive stress
net after removing five largest winners, stressed closed DD <=USD 150, and
five-day circular-block one-sided bootstrap p-value <=0.01.

Failure is terminal. V73 cannot be mirrored again or tuned on an opened stage.
V59/V60 remain immutable.

