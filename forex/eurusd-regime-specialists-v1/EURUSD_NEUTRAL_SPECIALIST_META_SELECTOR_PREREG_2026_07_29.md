# EURUSD Neutral specialist meta-selector preregistration

Frozen before the combined canonical candidate outcomes or selector result are
loaded.

## Question

Can one fixed, regularized, chronological meta-selector turn the eight frozen
Regime 1 specialists into a robust low-frequency portfolio without requiring
simultaneous agreement?

## Outcome-blind candidate universe

Only `entry_time_utc`, `side`, and `expert_id` are read from the immutable
signal-only census. Rows sharing an exact clock and side collapse to one
candidate with eight expert-membership flags. An opposite-side signal at the
same clock is represented as a feature rather than deleted. No source outcome,
EURUSD price, P&L, or oracle field is admitted when constructing this manifest.

## Fixed causal model

At each UTC calendar-month boundary, one standardized L2 logistic regression is
refit from scratch. Its labels are canonical 4-pip-stop / 6-pip-target outcomes
whose exits are strictly earlier than the boundary. It receives only the fixed
expert-membership, side, agreement-count, exact-clock conflict, UTC-clock, and
weekday features declared in the JSON contract. The model, `C=0.25`, solver,
600-row training floor, and inclusive 0.50 selection threshold are fixed.

At an eligible clock, the highest-probability candidate is selected only if it
meets 0.50. Routing is causal: earliest qualifying clock, no more than one
trade per UTC date, and no overlapping position. The execution contract is the
same conservative bid/ask M5 contract used by the exact-agreement experiment.

## Evaluation

The evaluation is 2023-01-01 through 2026-06-30. Models may expand using only
strictly prior closed outcomes. The result must report each year, the latest
six months, both sides, an extra 0.5-pip round-trip stress, removal of the best
5% of winners, drawdown, and evaluation-only oracle resemblance.

There is one run and no feature, threshold, expert, side, clock, or window
selection after outcome inspection. A historical pass cannot authorize demo or
broker activity; a separate prospective preregistration would still be
required.
