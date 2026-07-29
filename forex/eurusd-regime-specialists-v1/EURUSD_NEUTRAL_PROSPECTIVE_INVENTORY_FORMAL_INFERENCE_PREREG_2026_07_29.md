# EURUSD Neutral prospective inventory formal inference

Recorded with zero source, decision, path, oracle, or P&L records and before the
first scheduled operation.

## Defect closed by this layer

The component and portfolio validators count changes in calendar-month labels.
That convention can satisfy “12 months” near the start of July 2027 even though
the campaign begins on 30 July 2026. Those validators remain useful diagnostics,
but they cannot authorize the formal verdict. This superseding gate fixes the
earliest evaluation at `2027-07-30T00:00:00Z`, a full year after the prospective
start.

## Outcome-blind boundary

Before the exact time boundary and frozen sample counts are satisfied, the
formal status reports only decisions, signals, cash decisions, pending paths,
closed-trade counts, and counts by clock and side. It does not report returns,
wins, P&L, profit factor, payoff, drawdown, oracle resemblance, or risk results.

Formal evaluation requires at least 90 closed trades, 30 at 00:05, 20 at 06:05,
20 at 12:05, 20 on each side, no pending signal path, every closed-trade oracle
date, and complete component readiness. If counts are insufficient after the
time boundary, the campaign waits; it does not loosen a threshold.

## Frozen inference

The first complete formal evaluation uses 20,000 fixed-seed circular
moving-block bootstrap samples. The resampling unit is a UTC active trading day,
so all same-day clock outcomes remain together; blocks contain five active days.
Base and extra-0.5-pip returns are evaluated together.

In addition to every existing portfolio and risk gate, the one-sided 95% lower
bounds must satisfy:

- base profit factor greater than 1.00;
- stressed profit factor greater than 1.00;
- base expectancy greater than 0R;
- stressed expectancy greater than 0R.

The first complete result is written immutably with an evidence-chain hash and
is authoritative. Failure is `REJECTED_WITHOUT_RETUNING`; success is only
`INDEPENDENT_RESEARCH_REVIEW_REQUIRED`. This layer cannot declare demo
readiness, request data, or contact a broker.
