# EURUSD H4 frequency-completion portfolio v1 result

Status: **REJECTED**

The exact v1 construction reached 2,532 trades across 2,476 FX days, or 1.023
trades per day. It retained PF 1.210, 0.5-pip stressed PF 1.154, 1.0-pip
stressed PF 1.101, PF above 1 in every chronological block, 47.24% wins, 1.351
payoff, and 15.321R maximum drawdown.

It failed two frozen gates:

- best-5%-removed PF was 0.988 versus the required 1.000; and
- its smallest risk weight translated to 0.0075 lot versus the 0.01 broker
  minimum.

All added components passed their standalone gates. This exact risk allocation
is nevertheless rejected. The successor may preserve the immutable trade
ledger and change risk only; it may not delete any year, regime, session,
expert, or trade.
