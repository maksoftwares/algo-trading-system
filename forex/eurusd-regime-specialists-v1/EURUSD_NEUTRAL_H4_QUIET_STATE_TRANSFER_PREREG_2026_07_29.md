# EURUSD Neutral H4 quiet-state transfer preregistration

Frozen at `2026-07-29T12:51:38.2941701Z`, before the ten-year Dukascopy
transfer result was calculated.

## Question

Do either of the two already-frozen, low-frequency H4 quiet-state specialists
remain profitable when replayed without modification across the complete
2017-2026 EURUSD bid/ask history?

The two rules are:

1. the prior H4-chop Asia/London short control, using a 1.75 H1-ATR stop and
   1.25R target;
2. the prior H4-compression Asia/London short control, using a 1.75 H1-ATR stop
   and 2.0R target.

Both candidates were selected in earlier research, and the archived history
has been inspected. This experiment is therefore a retrospective causal
transfer and stability audit, not pristine out-of-sample evidence. Its purpose
is narrower: historical performance must be credible before future
confirmation is asked to carry any weight.

## Causal execution

- Only completed H1 and H4 bars may generate a signal.
- The H4 state becomes available only after its four-hour bar completes.
- The reference range is the six completed UTC hours from 00:00 through 05:59.
- The first qualifying completed H1 close below that range from 06:00 through
  09:59 may signal one short for the day.
- Entry is the exact next-hour M5 open.
- Bid/ask execution uses a 0.7-pip retail spread floor and 0.1-pip adverse
  slippage on entry and exit.
- Same-bar ambiguity resolves to the stop.
- The full twelve-hour M5 path must exist; otherwise the signal is cash.
- The known October 2024 suspect interval is quarantined.

## Frozen standard

A specialist must independently produce at least 100 trades, 45-55% wins,
1.35-1.75 realized payoff, PF at least 1.30, stressed PF at least 1.15, PF above
one in every chronological block, positive recent twelve-month performance,
at least 55% positive active months, PF at least one after removing the largest
5% of winners, and no more than 15R closed-trade drawdown.

No clock, side, year, threshold, stop, target, regime, or subgroup may be
changed after the result opens. The two candidates may form a portfolio only
if each passes standalone.

Even a pass is historical research only. It cannot authorize a demo attachment,
account access, or an order.
