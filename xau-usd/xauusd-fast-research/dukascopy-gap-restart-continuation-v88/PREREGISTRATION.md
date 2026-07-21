# V88 Dukascopy Gap-Restart Continuation Preregistration

## Incremental Hypothesis

V87 rejected continuation after a continuous quote burst. V88 was independently
defined earlier as Capital V26 and uses a mechanically disjoint clock: a short
liquidity interruption followed by a directional restart. V88 does not alter or
inspect Capital V26 forward outcomes and cannot tune V59/V60.

## Fixed Causal Candidate

A restart begins at the first XAUUSD quote after a gap from 2,001 through 5,000
milliseconds. During the first 1,000 milliseconds from that restart, the
hash-locked V26 constructor uses only restart-to-current quotes and requires at
least five nonzero mid updates, absolute signed update imbalance at least 0.60,
absolute displacement at least USD 0.30, agreement between imbalance and
displacement sign, and current spread no more than USD 0.35. It keeps the first
qualifying quote per restart and first event per fixed four-hour UTC block.
Direction follows the restart imbalance. The research session is 07:00-18:00
UTC and at most four candidates can exist per UTC date.

## Outcome-Blind Density Gate

There is one fixed rule and no parameter grid. January 2019 may reveal only
source quality, candidate timestamps, frequency, active-day share, and direction
balance. It must produce 0.85-4.00 candidates per eligible weekday, activate on
at least 60% of days, and allocate at least 20% to each direction. Failure ends
V88 before any economic outcome is opened.

## Economic Label And Gates

Entry is the first quote strictly after the candidate within two seconds. Exit
is the first quote at or after 120 seconds within two seconds. Long pays entry
ask and receives exit bid; short receives entry bid and pays exit ask. Base and
stress deduct USD 0.05 and USD 0.15 slippage per side respectively, plus USD
0.30 ticket cost, at one ounce reference exposure.

Development must produce at least 500 resolved trades, at least 0.85/day, base
PF at least 1.30, stress PF at least 1.20, positive winner-removed stress P&L,
at least 60% positive months, both halves above stress PF 1.10, stressed closed
drawdown no more than USD 250, and the locked multiplicity-adjusted daily block
bootstrap gate. Failure is terminal. Only an unchanged survivor may open later
stages and the shared V59/V60 audit.

No ML training, prediction, EA consumption, demo/live execution, paid data, or
broker action is authorized.
