# V76 Treasury-Bond-to-XAU Event-Time Catch-Up Preregistration

Date: `2026-07-20`

## Hypothesis

Earlier macro studies used completed M5/H1 aggregate bond state. V76 tests a
distinct causal mechanism: a raw U.S. Treasury bond CFD quote shock occurs while
the strictly prior XAU quote has not completed the expected same-direction
response. A rising bond price implies falling yields and an expected rising gold
price; a falling bond price implies an expected falling gold price.

At a bond event timestamp, the bond and XAU horizon baselines are the last quotes
at or before the horizon boundary. The current XAU observation is strictly
earlier than the bond event. Entry is the first XAU quote strictly later than the
event. No future quote or outcome participates in candidate selection.

## Outcome-Blind Calibration

January 2019 is calibration only. Exactly 1,000 policies are registered from:

- source horizon: 1, 2, 5, 10, or 20 seconds;
- minimum absolute bond move: 0.1, 0.2, 0.3, 0.4, or 0.5 bps;
- minimum same-direction innovation: 0.1, 0.2, 0.3, 0.4, or 0.5 bps;
- maximum already-completed XAU response ratio: 0, 0.25, 0.50, or 0.75; and
- minimum bond quote count: 2 or 5.

Selection uses candidate timestamps, frequency, active-day share, and direction
balance only. XAU post-entry outcomes remain unopened. The deterministic ranking
targets 0.80 candidate/day, then prefers larger shock and innovation thresholds,
smaller completed response, more source quotes, shorter horizons, and policy ID.

## Frozen Execution

- one earliest candidate per UTC date from 07:00 through 18:00 UTC;
- first side-correct XAU quote strictly after the source event, within one second;
- 0.5 completed-M5 ATR stop, four-spread minimum, and USD 1 minimum distance;
- 1.5R target and 15-minute maximum hold;
- one ounce, USD 0.30 ticket cost, USD 0.35/day holding cost, and 0.05R stress;
- no entry with initial risk above USD 50.

## Sequential Evidence

- development: February 2019 through June 2022;
- confirmation: July 2022 through June 2023;
- validation: July 2023 through June 2024;
- exam: July 2024 through June 2026.

Each stage remains sealed until all earlier gates pass. Required frequency is
0.65-1.00 resolved trades per eligible weekday. Economic gates require positive
base/stress net, base PF at least 1.30, stress PF at least 1.20, positive-day
share at least 45%, positive-month share at least 60%, each direction at least
20%, each chronological-half stress PF at least 1.05, positive stress net after
removing the five largest winners, stressed closed drawdown no more than USD 150,
and a five-day block-bootstrap one-sided p-value no greater than 0.005.

Failure is terminal for the registered direction. No threshold, timing, exit,
cost, quota, or same-version rescue is allowed. A fixed opposite-direction test
may use only periods unopened by V76 and must be preregistered separately.
V59/V60 remain byte-identical and outside selection.
