# EURUSD Neutral 06:00-08:00 UTC range-breakout execution preregistration

Status: `FROZEN_BEFORE_FIRST_FORWARD_PATH_OR_PNL`

The v1.1 outcome-blind census passed all capacity gates and was committed and
pushed before this execution implementation was created.

## Fixed execution

- Candidate entry: exact frozen M5 entry open, verified against the census
  decision-time price.
- Entry cost: at least 0.7 pip retail spread plus 0.1 pip adverse slippage.
- Stop: the candidate's frozen ATR/range structure stop.
- Target: exactly 1.5 times the candidate risk distance.
- Maximum hold: 12 hours.
- Same-bar ambiguity: stop first.
- Exit slippage: 0.1 pip adverse on stop, target, or time exit.
- One open position; at most two executed trades per UTC date.
- Missing entry or incomplete exact 12-hour path: cash.
- Known suspect October 2024 path overlap: cash.

## Fixed evaluation

The result must report:

- overall and chronological-window trade count, win rate, realized payoff,
  PF, expectancy, net R, and max drawdown;
- both directions separately;
- an extra 0.5-pip round-trip stress;
- removal of the top 5% of trades by R;
- latest-six-month performance;
- exact and ±15-minute same-side one-to-one Neutral oracle overlap.

All performance gates are copied unchanged from the hash-locked v1 contract.
The oracle is evaluation-only and cannot influence a signal, side, entry,
exit, or subgroup.

## Decision rule

Every frozen gate must pass. A failure rejects this exact family. No hour,
weekday, side, year, direction, risk, target, or volatility subgroup may be
selected after opening the result.

Even a historical pass cannot authorize demo or live trading. It would only
justify a separate prospective freeze.
