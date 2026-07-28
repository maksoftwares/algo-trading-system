# EURUSD Neutral independent prospective validation preregistration

Date: `2026-07-28`

Status: `FROZEN_BEFORE_PROSPECTIVE_START_AND_FIRST_SIGNAL`

This is an outcome-blind validation layer for the unchanged EURUSD Neutral
macro/cross-asset specialist. It does not alter forecasts, signals, entries,
stops, targets, sizing, trade routing, or the Regime 1 ownership rule. It
cannot fetch data, write evidence, or call a broker.

The existing campaign admission remains a research checkpoint. This stricter
layer closes the remaining demo-quality evidence gaps before any prospective
outcome exists.

## Frequency policy

There is no trades-per-day gate. Frequency is reported as closed trades,
active trade days, elapsed weekdays, and trades per elapsed weekday. The
strategy should remain in cash whenever its frozen three-way agreement is
absent.

## Path-level floating equity

Every closed trade must link to its immutable, continuous 12-hour bid/ask M5
path. Long floating marks use executable bid prices; short marks use
executable ask prices. The same spread floor and adverse slippage as the
frozen execution contract apply.

Intrabar order is resolved adversely for drawdown:

- a stop bar terminates at the already frozen stop fill, so movement after
  that fill is excluded;
- a target bar records the adverse extreme before the target fill; and
- an unresolved time-exit bar assumes favorable-before-adverse ordering
  before its closing fill.

This produces base and extra-half-pip stressed floating-equity drawdown on a
fixed `$1,000` research balance at `0.01` lot. Missing paths fail closed.

## Frozen validation gates

Review is prohibited before 12 calendar months and 30 closed trades. All
following checks must pass:

- 45%-55% win rate and 1.35-1.75 realized payoff;
- base PF at least 1.30 and positive expectancy;
- extra-half-pip PF at least 1.15;
- trailing-12-month PF at least 1.15 with positive net R;
- at least eight LONG and eight SHORT trades, with each side PF at least 1.0;
- at least 55% of active months profitable;
- PF at least 1.0 after removing the top 5% of winners;
- no month contributes more than 50% of positive monthly profit;
- base floating drawdown no more than 5% and stressed floating drawdown no
  more than 10%; and
- a fixed-seed, 10,000-path, circular five-trade block bootstrap over 250
  trades has less than 1% probability of breaching 10% drawdown.

## Oracle approximation

All closed trade dates must have safely known, evaluation-only oracle labels.
Same-day/same-side precision must be at least 50%.

Precision is also compared with the exact random-side base rate for each
date. A date with only one Neutral oracle side has a 50% random-side match
probability; a date with both sides has 100%; a date with neither has 0%.
The strategy must have strictly positive precision lift and a one-sided exact
Poisson-binomial random-side tail probability no greater than 10%.

Entry-time precision within 15, 60, and 240 minutes of the nearest same-side
Neutral oracle trade is reported but cannot change or filter a signal.

## Decision policy

Missing paths, missing oracle dates, insufficient sample, or any failed gate
cannot be repaired with a retrospective family, side, hour, threshold, or
period filter. A passing result triggers independent research review only.
It does not declare controlled-demo readiness and never authorizes an order.
