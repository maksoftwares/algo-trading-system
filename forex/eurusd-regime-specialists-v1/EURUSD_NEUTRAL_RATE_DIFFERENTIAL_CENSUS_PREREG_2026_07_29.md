# EURUSD Neutral rate-differential census preregistration

Frozen before the Neutral candidate count and before any EURUSD price, return,
oracle, or P&L is loaded.

The signal uses only official U.S. Treasury and ECB two-year rates on exact
common observation dates. At each causally Neutral 00:00 UTC timestamp, the
latest admissible observation date must be at least two calendar days old. The
change from the preceding common observation must have absolute magnitude of at
least five basis points.

- Wider U.S.-minus-euro spread: SHORT EURUSD.
- Narrower U.S.-minus-euro spread: LONG EURUSD.
- Zero or smaller move: cash.

There is one candidate at most per Neutral date. Threshold, direction mapping,
lag, and clock are fixed. The census reads only `entry_time_utc` and `side`
from the immutable Neutral timestamp source and does not inspect market
outcomes.

Passing every frozen capacity gate permits only a separately hash-locked
execution experiment. It does not authorize P&L claims, demo trading, or broker
action.
