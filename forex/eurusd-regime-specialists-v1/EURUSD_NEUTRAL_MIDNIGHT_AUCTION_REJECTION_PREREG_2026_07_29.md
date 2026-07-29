# EURUSD Neutral midnight auction-rejection preregistration

Status: `FROZEN_BEFORE_FIRST_CANDIDATE_COUNT_AND_ANY_OUTCOME`

## Mechanism

The rule observes only the completed 00:00, 00:05, and 00:10 EURUSD M5
bars. At 00:15 it trades a failed opening auction:

- Long only when a downward excursion of at least three pips dominates, the
  completed close returns to or above the midnight open, and the lower
  rejection wick owns at least 55% of the opening range.
- Short only when the symmetric upward rejection condition holds.
- Opening ranges above 20 pips route to cash.
- Every other shape routes to cash.

This is distinct from the retired prior-24-hour fade: it uses no prior-day
close, extreme, body, side, risk, or outcome. It is also not an inversion of
the failed opening-drive continuation family; it requires a wick-dominant
reclaim through the open.

## Causality and ownership

All three observation bars must be complete before the exact 00:15 entry.
The latest fully known hourly classifier state must be Neutral, unresolved,
non-shock, non-compressed, and no more than four hours stale.

## Fixed risk

- Exact 00:15 M5 open with 0.7-pip spread floor and 0.1-pip adverse entry
  slippage.
- Stop beyond the completed auction extreme and at least four pips away.
- Maximum risk 15 pips.
- Target 1.5R, six-hour maximum hold, and stop-first ambiguity handling.
- One position and one trade per UTC date.

## Stage boundary

The first pass may count only completed observations, causal ownership,
sides, timestamps, and decision-time risk. It may not load any forward
path, exit, return, P&L, or oracle row.

If all capacity gates pass, execution still requires a separate hash lock,
commit, and push. Failure retires the exact family without repair.
