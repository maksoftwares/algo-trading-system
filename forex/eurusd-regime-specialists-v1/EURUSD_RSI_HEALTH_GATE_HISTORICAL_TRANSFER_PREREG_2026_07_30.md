# EURUSD RSI health-gate historical transfer preregistration

Date: 2026-07-30

Status: **FROZEN_BEFORE_TRANSFER_RESULT**

Demo-order authorization: **false**

## Purpose

The strongest frequency/edge diagnostic used the last 30 completed shadow
trades to enable the existing M15 RSI-long sleeve only while trailing PF was
at least 1.05. Combined with the protected M15 regime sleeve, it produced
0.856 trades/weekday and PF 1.487 on the two-year Capital.com replay.

That gate was selected after comparing 500 historical variants. This test does
not pretend it is pristine. It asks a narrower question: does the exact frozen
rule transfer unchanged to the independently reconstructed 2017-2024
Dukascopy bid/ask archive?

## Exact reconstruction

The source-locked `ForexMeanReversionScout` contract is reconstructed without
parameter search:

- completed M15 RSI(14) at or below 30;
- completed close below the 20-bar band midpoint;
- body fraction at least 0.40;
- long only, with entry on the next executable bar;
- entry hours 01:00, 07:00, and 21:00 UTC blocked;
- one open position, at most 20 entries per UTC date;
- stop below the preceding six M15 lows or 1.40 ATR, with 3-70-pip bounds;
- target 0.80R;
- bid/ask execution, stop-first ambiguity, and 0.1 pip adverse slippage per
  side.

The selected health gate remains global lookback 30 and trailing PF 1.05.
Rejected shadow outcomes remain observable, and only exits completed by the
candidate entry time may enter its gate state.

## Required evidence

Before economics count, the Dukascopy reconstruction must cover at least 60%
of the 633 broker entries with a qualifying same-side signal within 15
minutes, and its raw trade count must remain within 0.50-1.50 times the broker
count.

The health-gated 2017-2024 transfer must then produce at least 600 trades and
0.40 trades/weekday, PF at least 1.15, stressed PF at least 1.05, PF above
1.00 in all three chronological blocks, latest-earlier-12-month PF at least
1.00, best-5%-removed PF at least 1.00, at least 55% positive active months,
and drawdown no greater than 30R.

The separate 2024-2026 cross-broker portability window must retain at least
0.40 trades/weekday, PF at least 1.00, and stressed PF at least 0.95.

## Decision boundary

No failed gate may be repaired. A pass would strengthen the historical
backtest and justify a disarmed combined-router build, but it would still
require fresh prospective evidence before demo orders.
