# EURUSD Neutral prospective directional falsification preregistration

Date: `2026-07-28`

Status: `FROZEN_BEFORE_PROSPECTIVE_START_AND_FIRST_SIGNAL`

This evaluation-only control asks whether the frozen Regime 1 strategy
selects the economically correct direction, rather than merely benefiting
from generic post-release volatility.

It cannot create, filter, reverse, resize, delay, or cancel a primary trade.
It reads a closed trade only after the immutable 12-hour bid/ask path is
available and creates an offline counterfactual.

## Frozen counterfactual

For every closed primary trade:

- use the exact same signal ID, M5 entry timestamp, 12-hour path, and risk
  distance;
- reverse only `LONG` to `SHORT` or `SHORT` to `LONG`;
- enter at executable bid/ask with the same 0.7-pip spread floor and 0.1-pip
  adverse slippage per side;
- use the same 1.5R target and 12-hour hold;
- resolve a same-bar stop and target as a stop; and
- report the same extra-half-pip round-trip stress.

A missing, discontinuous, hash-mismatched, or time-mismatched path fails
closed. The counterfactual is never persisted into the primary signal or
trade ledger and cannot affect future decisions.

## Frozen directional test

Review is prohibited before 12 calendar months and 30 closed primary trades.
All checks must pass:

- primary PF at least 1.30;
- primary PF exceeds opposite-side PF by at least 0.15;
- primary expectancy is strictly greater than opposite-side expectancy;
- primary win rate is strictly greater than opposite-side win rate; and
- a one-sided paired randomization test of
  `primary R - opposite-side R` has `p <= 0.10`.

The paired null says that the primary and opposite-side labels are
exchangeable inside each event. Up to 20 pairs use exact sign enumeration.
Larger samples use 100,000 fixed-seed sign vectors with seed `20260728` and a
plus-one finite-simulation correction.

Frequency is reported but has no gate. No historical P&L, parameter search,
or outcome-based filter is allowed.

Passing means only that the directional hypothesis survives independent
research review. Failure rejects the exact directional rule without
retuning. Neither result authorizes demo or live broker action.
