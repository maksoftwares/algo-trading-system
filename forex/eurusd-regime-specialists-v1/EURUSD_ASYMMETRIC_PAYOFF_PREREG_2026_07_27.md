# EURUSD asymmetric-payoff preregistration

Status: `LOCKED_BEFORE_1P5R_OUTCOME_INSPECTION`

## Objective

Test the user's requested geometry directly:

- realized win rate around 50%, defined as 45% through 55%;
- realized average winning R divided by average losing R around 1.5, defined as 1.35 through 1.75;
- portfolio profit factor at least 1.30 after realistic costs;
- at least one completed trade per Monday-Friday UTC trading day.

“Profit ratio” is measured as realized average win / average loss. Profit factor is reported separately.

## Frozen information boundary

All EURUSD history through June 2026 has already been inspected. This is adaptive development evidence, not an untouched exam and not permission for demo or live trading.

The signal clocks, thresholds, long-only directions, causal regime classifier, exclusive ownership, quarantine, and priority are inherited unchanged from `frozen_two_clock_ensemble.json`. Its outcome-blind census already passed at 6,035 owned raw signals and 3.09 signals per weekday.

## Only allowed change

- replace the inherited 0.80R target with 1.50R;
- close any still-open trade after 12 hours at executable M5 bid;
- retain the existing ATR/recent-low stop;
- retain a 0.70-pip minimum retail spread and 0.10-pip adverse slippage per side;
- retain stop-first treatment for same-bar stop/target ambiguity.

No entry filter, hour, regime owner, classifier threshold, stop distance, or cost assumption may change after outcome inspection.

## Admission

Each specialist must have at least 75 trades in every chronological window. In every window it must have:

- win rate from 45% through 55%;
- realized payoff ratio from 1.35 through 1.75;
- PF at least 1.30;
- expectancy above 0.05R.

It must also keep overall drawdown at or below 20R, remain positive after removing the top 5% of winners, and remain positive after another 0.50-pip round trip.

Only admitted specialists may enter the portfolio. The portfolio must retain the same win-rate/payoff bands, PF at least 1.30, positive net in every window, and at least one actual trade per weekday.

Failure is reported without target, hold-time, regime, or threshold repair.
