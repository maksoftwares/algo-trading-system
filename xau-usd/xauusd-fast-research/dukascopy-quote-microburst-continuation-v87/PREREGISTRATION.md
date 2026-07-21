# V87 Dukascopy Quote Microburst Continuation Preregistration

## Incremental Hypothesis

The existing portfolio does not use millisecond quote-update imbalance as an
entry clock. V87 replicates the still-unexposed Capital V24.1 continuation
hypothesis on verified Dukascopy XAUUSD history. It does not alter or inspect
Capital V24.1 forward outcomes and cannot tune V59/V60.

## Causal Candidate

For each XAUUSD quote in 07:00-18:00 UTC, V87 uses only quotes at or before that
timestamp. Over a fixed trailing lookback, it counts nonzero mid updates,
calculates the mean sign of those updates, measures mid displacement in basis
points, checks spread and quote continuity, and requires imbalance and
displacement to agree in sign. A raw event is the first false-to-true crossing
of the complete gate. Only the first raw event per UTC date is retained. Long
follows positive imbalance; short follows negative imbalance.

## Outcome-Blind Registry

January 2019 registers exactly `4 x 5 x 5 x 5 x 2 = 1,000` policies:

- lookback: 1, 2, 5, or 10 seconds;
- minimum nonzero mid updates: 5, 10, 15, 25, or 40;
- minimum absolute signed imbalance: 0.50, 0.60, 0.70, 0.80, or 0.90;
- minimum absolute displacement: 1.00, 2.00, 3.00, 5.00, or 7.50 bps; and
- maximum spread: 3.00 or 5.00 bps.

Selection uses candidate frequency, active-day share, direction balance, and a
fixed deterministic tie-break only. No post-candidate quote or P&L is opened.

## Economic Label And Gates

Entry is the first quote strictly after the candidate within two seconds. Exit
is the first quote at or after 120 seconds within two seconds. Long pays entry
ask and receives exit bid; short receives entry bid and pays exit ask. Base and
stress deduct USD 0.05 and USD 0.15 slippage per side respectively, plus USD
0.30 ticket cost, at one ounce reference exposure.

Development must produce at least 550 resolved trades, at least 0.85/day, base
PF at least 1.30, stress PF at least 1.20, positive stress expectancy after the
five largest winners are removed, at least 60% positive months, both halves
above stress PF 1.10, stressed closed drawdown no more than USD 250, and the
locked multiplicity-adjusted daily block-bootstrap gate. Failure is terminal.
Only an unchanged survivor may open later stages and the shared V59/V60 audit.

No ML training, prediction, EA consumption, demo/live execution, paid data, or
broker action is authorized.
