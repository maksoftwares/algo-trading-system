# V78 FX Dollar-Consensus-to-XAU Event-Time Preregistration

Date: `2026-07-20`

## Hypothesis

The retired DXY, silver, and Treasury-bond campaigns used one external source at
a time. V78 requires two liquid FX majors to agree on dollar direction before a
gold trade exists. EURUSD rising while USDJPY falls implies dollar weakness and
an expected XAU long; EURUSD falling while USDJPY rises implies dollar strength
and an expected XAU short. Any disagreement is an abstain state.

EURUSD is the fixed event clock. At its event timestamp, both FX baselines use
the last quotes at or before the horizon boundary, the current USDJPY quote is
at or before the event, and the current XAU quote is strictly before the event.
Entry is the first side-correct XAU quote strictly after the event. No future
quote or post-entry outcome participates in candidate selection.

## Outcome-Blind Calibration

July and August 2018 are calibration only. Exactly 1,000 policies are registered:

- horizon: 1, 2, 5, 10, or 20 seconds;
- minimum absolute move in each FX leg: 0.05, 0.10, 0.15, 0.20, or 0.25 bps;
- minimum sum of both absolute FX moves: 0.10, 0.20, 0.30, 0.40, or 0.50 bps;
- maximum already-completed signed XAU response: 0, 0.25, 0.50, or 0.75 of
  the smaller FX-leg move; and
- minimum quote count in each FX leg: 2 or 5.

Selection uses candidate timestamps, frequency, active-day share, and direction
balance only. The deterministic ranking targets 0.80 candidate/day, then prefers
larger consensus and leg thresholds, smaller completed XAU response, more source
quotes, shorter horizons, and policy ID. Post-entry XAU outcomes remain unopened.

## Frozen Execution And Gates

The earliest candidate per UTC date from 07:00 through 18:00 UTC uses the first
XAU quote strictly after the event, within one second. Exit geometry is fixed at
a 0.5 completed-M5 ATR stop, four-spread minimum, USD 1 minimum stop, 1.5R target,
and 15-minute maximum hold. Economics use one ounce, USD 0.30 ticket cost, USD
0.35/day holding cost, 0.05R stress slippage, and USD 50 maximum initial risk.

Sequential stages are development from September 2018 through June 2021,
confirmation from July 2021 through June 2022, validation from July 2022 through
June 2023, and exam from July 2023 through June 2024. Each later stage remains
sealed until all prior gates pass.

Required frequency is 0.65-1.00 resolved trades per eligible weekday. Economic
gates require positive base/stress net, base PF at least 1.30, stress PF at least
1.20, positive-day share at least 45%, positive-month share at least 60%, each
direction at least 20%, each chronological-half stress PF at least 1.05, positive
stress net after removing the five largest winners, stressed closed drawdown no
more than USD 150, and a five-day block-bootstrap one-sided p-value no greater
than 0.0025.

Failure is terminal for the registered direction. No threshold, timing, exit,
cost, quota, or same-version rescue is allowed. V59/V60 remain byte-identical
and outside selection.
