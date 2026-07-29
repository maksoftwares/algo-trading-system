# Prospective EURUSD Neutral inventory-unwind 00:05 expert

Status: `FROZEN_BEFORE_PROSPECTIVE_START`

The rejected historical 00:15 family strongly resembled Regime 1 oracle
timing but lost overall. Its historical years are fully exposed, so this
earlier-clock successor is outcome-informed and may never be backtested on
them.

Beginning 30 July 2026, the expert will use only:

- the completed prior 20:00-00:00 EURUSD tick window;
- the previously frozen causal Neutral ownership classifier;
- a four-pip absolute displacement floor;
- the opposite side of the completed displacement;
- a decision frozen by 00:04 UTC and shadow entry at 00:05 UTC;
- a six-pip stop, nine-pip target, six-hour hold, executable bid/ask prices,
  spread floor, spread ceiling, and adverse slippage.

Late, missing, non-Neutral, stale, or subthreshold evidence produces cash.
No late source may be backfilled into a signal.

Admission requires at least 12 calendar months, 30 closed trades, eight
trades per side, the frozen economic and robustness gates, and separately
validated same-day and 15-minute Regime 1 oracle resemblance. Frequency is
reported but is not a gate.

This is shadow research only. It cannot place, recommend, or authorize a
demo or live broker order.
