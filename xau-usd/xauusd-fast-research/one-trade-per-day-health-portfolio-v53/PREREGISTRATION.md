# V53 Preregistration

## Purpose

Test whether the unchanged V50 Core plus three non-Core historical sleeves can
reach at least one executed trade per weekday without allowing profitable Core
trades to conceal a negative marginal add-on portfolio.

## Evidence status

All source outcomes have been exposed by earlier research. V53 is therefore a
post-outcome historical portfolio-governance test and does not claim a pristine
holdout. The exact V53 policy is locked before the V53 account drawdown circuit
is evaluated. The result is terminal and cannot be repaired in place.

## Fixed sleeves

- `V7_SWING_HEALTH`: the fixed V7 opening-range pullback swing rule, with a
  100-completed-shadow-trade trailing PF gate and a USD 30 initial-risk cap.
- `V8_RETEST_HEALTH`: the fixed `V8_0002` retest/intraday rule, with the same
  100-trade causal health gate and a USD 20 initial-risk cap.
- `V25_CHOP`: the sealed V25 raw-tick chop finalist, capped at USD 30 risk.

The health gate uses only candidate exits strictly earlier than the current
signal. A sleeve is active only when trailing PF is at least 1.0 and trailing
net is positive. Shadow outcomes are observable research states; rejected
trades never contribute account P&L.

## Account controls

- V50 is unchanged.
- At most two add-on positions may be open.
- Add-on initial risk may not exceed USD 45 in aggregate.
- At most two add-on entries may be accepted per UTC date.
- New add-ons suspend when causal account closed drawdown reaches USD 240 and
  resume only after it recovers to USD 200 or less.
- The USD 240/200 circuit is derived from the pre-existing USD 300 ceiling; it
  is not selected from the V53 result.

## Pass definition

Development-2, confirmation, and final must each retain positive marginal
add-on net, add-on PF at least 1.15, positive net after removing the five largest
winners, combined PF at least 1.5, combined closed drawdown at most USD 300,
and positive combined net after removing the five largest winners. Each of the
three windows must reach at least one combined trade per weekday. Final add-on
drawdown may not exceed USD 150 and final combined positive-month share must be
at least 50%.

No result authorizes Python serving, an EA, demo trading, live trading, or
broker action. Complete shared-account floating-equity evidence and prospective
confirmation remain mandatory.

