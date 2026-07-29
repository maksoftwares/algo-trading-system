# EURUSD Neutral late-session inventory-unwind preregistration

Frozen before the first candidate count and before every outcome.

## Independent mechanism

This is not a repair of the rejected midnight-wick rule. For every UTC
weekday it measures the completed 20:00-23:55 UTC EURUSD displacement. It
then observes the completed 00:00, 00:05, and 00:10 M5 bars. A trade is
eligible at 00:15 only when those first 15 minutes have already started a
meaningful unwind opposite the late-session displacement.

- Late down displacement plus at least +1.5 pips of confirmation: `LONG`.
- Late up displacement plus at least -1.5 pips of confirmation: `SHORT`.
- Confirmation must retrace at least 15% of the late displacement.
- Anything else is `CASH`.

## Outcome-blind capacity ladder

The absolute late-session displacement thresholds are permanently ordered
`12`, `10`, then `8` pips. The census must select the first threshold that
passes every frozen capacity gate. It may not inspect a stop/target path,
return, P&L, oracle row, or profitability statistic. If none passes, the
8-pip table is retained only to document failure and execution is forbidden.

## Frozen execution

The exact 00:15 bid/ask M5 open is used with a 0.7-pip retail spread floor
and 0.1-pip adverse slippage per side. The stop is beyond the completed
first-15-minute extreme, with a four-pip minimum and 12-pip maximum risk.
Target is 1.5R, maximum hold is six hours, and same-bar ambiguity is
stop-first. There can be at most one position per UTC date.

## Admission boundary

Even a passing capacity census permits only a separately implemented,
hash-locked historical execution. Promotion still requires every frozen
chronological, side, cost, robustness, drawdown, latest-six-month, and
oracle-resemblance gate. This research cannot place broker, demo, or live
orders.
