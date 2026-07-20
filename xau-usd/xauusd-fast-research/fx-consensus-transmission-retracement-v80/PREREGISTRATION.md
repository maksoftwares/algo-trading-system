# V80 FX Consensus Transmission-Retracement Preregistration

Date: `2026-07-20`

## Hypothesis

V78/V79 proved that immediate entry after the first daily FX-consensus event is
dense but uneconomic in both directions. V80 does not change those entries or
rescue their thresholds. It defines a different causal event: after a locked V78
source impulse, XAU must first move in the implied direction and then retrace a
fixed fraction of its running favorable excursion. The retracement quote is the
decision time; entry is the first side-correct XAU quote strictly afterward.

## Fixed Source Event

V80 inherits V78 policy `H01000__LM025__CS050__RR000__QC05` exactly. EURUSD and
USDJPY must agree on dollar direction over the same one-second horizon, each leg
must move at least 0.25 bps, their absolute moves must sum to at least 0.50 bps,
the strictly prior XAU response ratio must be at most zero, and both FX legs must
contain at least five quotes. All V78 source timestamp and staleness rules remain
unchanged. Unlike V78, V80 may evaluate every qualifying source event until the
first completed transmission-retracement pattern of the UTC date.

## Outcome-Blind Timing Calibration

July-August 2022 is timing calibration only and begins exactly after V79's
exposed development cutoff. Exactly 100 timing policies are registered from:

- XAU transmission: 0.25, 0.50, 0.75, 1.00, or 1.50 bps;
- retracement from running favorable excursion: 25%, 40%, 50%, 60%, or 75%;
- maximum source-event-to-retracement time: 10, 20, 30, or 60 seconds.

Selection uses only candidate completion times, frequency, active-day share,
and direction balance. The deterministic ranking targets 0.80 candidate/day,
then prefers larger transmission, deeper retracement, shorter completion time,
and policy ID. Post-entry outcomes remain unopened.

## Frozen Economics And Evidence

Execution retains the V78 bid/ask, stop, target, hold, size, cost, and stress
geometry. Development is September 2022 through June 2023; validation is July
2023 through June 2024. Validation remains sealed unless every development gate
passes. Both stages require 0.65-1.00 resolved trades per eligible weekday,
positive base/stress net, base PF at least 1.30, stress PF at least 1.20,
positive-day share at least 45%, positive-month share at least 60%, each
direction at least 20%, each half stress PF at least 1.05, positive stress net
after removing the five largest winners, stressed closed drawdown no more than
USD 150, and five-day block-bootstrap p-value no greater than 0.00125.

The archive ends in June 2024. A historical pass is provisional and still needs
untouched forward proof. Failure is terminal for this mechanism. V59/V60 remain
byte-identical and outside selection.
