# EURUSD Neutral prospective validation V1.1 preregistration

Date: `2026-07-28`

Status: `FROZEN_BEFORE_PROSPECTIVE_START_AND_FIRST_SIGNAL`

The V1 validator correctly tests profitability, robustness, same-day oracle
direction, and a random-side null. Its temporal metrics were diagnostic only.
Consequently a strategy could pass while entering many hours from every
Regime 1 oracle trade, and multiple strategy trades could reuse one oracle
row. That does not establish oracle imitation.

V1.1 supersedes only the evaluation layer. The strategy, source evidence,
forecast, ownership, entry, stop, target, sizing, and trade routing are
unchanged. No historical P&L or prospective outcome existed at this lock.

For each UTC date and side, V1.1 finds the maximum-cardinality one-to-one
matching between closed strategy trades and Neutral oracle trades, then
minimizes total absolute entry-time distance. Oracle rows cannot be reused.
Precision and recall are reported at 15, 60, and 240 minutes. Recall remains
diagnostic because frequency is negotiable.

The primary imitation gate is the 60-minute window:

- at least 25% one-to-one precision;
- strictly positive precision lift over a uniform random M5 time and random
  side on the same oracle date; and
- an exact one-sided Poisson-binomial tail probability no greater than 10%.

The random null counts the exact covered slots on the 288-point UTC M5 entry
grid for both sides. It is exact only with at most one strategy trade per UTC
date; otherwise the gate fails closed. Completed oracle dates remain required.

These gates are additional to every V1 profitability and robustness gate.
Failure prohibits a Regime 1 imitation claim and retrospective repair.
Passing still triggers research review only and does not authorize demo or
live broker action.
