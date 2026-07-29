# EURUSD Neutral late-session inventory-unwind V1.1 execution preregistration

Status: `FROZEN_BEFORE_FIRST_FORWARD_PATH_OR_PNL`

The outcome-blind census selected the predeclared four-pip floor, passed all
capacity gates, and was committed and pushed before this execution contract.

## Fixed evaluation

- Exact frozen 00:15 M5 entry price.
- Frozen completed-first-15-minute structure stop.
- Fixed 1.5R target and six-hour maximum hold.
- Executable bid/ask path with stop-first same-bar handling.
- A 0.7-pip spread floor and 0.1-pip adverse slippage per side.
- One position and one trade per UTC date.
- Missing or incomplete exact path routes to cash.
- The inherited suspect October 2024 interval routes to cash.

The evaluator must report overall, chronological, side, extra-cost,
top-winner-removal, latest-six-month, and one-to-one Neutral oracle metrics.
All performance gates are copied unchanged from the census contract.

Every gate must pass. Failure retires the exact signal; no direction,
threshold, confirmation, retracement, risk, side, weekday, year, or
volatility subgroup may be repaired after the result.

Even a historical pass cannot authorize demo or live trading. It would only
justify a separate prospective freeze.
