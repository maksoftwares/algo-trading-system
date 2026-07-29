# EURUSD Neutral Prospective Inventory Clock-Transfer Preregistration

Recorded on 2026-07-29 before the first eligible source window begins at
2026-07-30 02:00 UTC.

## Question

Does the already frozen causal inventory-unwind mechanism transfer from the
00:05 UTC primary clock to a fixed two-clock portfolio at 06:05 and 12:05 UTC
on causally owned Regime-1/Neutral weekdays?

This is an outcome-informed family because the losing historical late-session
parent and its 00:05 forward successor were already designed. No outcome from
the 06:05 or 12:05 transfer rules has been inspected. Historical backtesting,
historical EURUSD P&L loading, parameter search, and clock selection are
forbidden.

## Frozen specialist

For each UTC weekday and each clock:

1. Use the immutable daily Neutral ownership record that was observable by
   00:04 UTC. Missing, late, stale-at-cutoff, or non-Neutral ownership means
   cash.
2. Measure EURUSD midpoint displacement over the four fully completed hours
   immediately before the clock hour.
3. If displacement is at least +4 pips, shadow short. If it is at most -4
   pips, shadow long. Otherwise remain cash.
4. Create the decision at HH:04 and use the first bid/ask tick at or after
   HH:05.
5. Require actual entry spread no greater than 1.5 pips, impose a 0.7-pip
   retail spread floor and 0.1-pip adverse slippage on each side.
6. Use a 6-pip stop, 9-pip target, six-hour maximum hold, exact tick ordering,
   adverse stop-first handling, and the correct bid/ask side.

The frozen clocks are 06:05 and 12:05 UTC. They form one equal-policy,
unweighted specialist. The 06:05 and 12:05 outcomes may be reported
separately for failure diagnosis, but neither clock may be deleted, selected,
reweighted, repaired, or promoted on its own after outcomes.

The six-hour time exit of one clock is processed before the next clock's entry,
so the transfer specialist has at most one open position. It is shadow-only
and cannot contact a broker.

## Prospective evidence and immutability

Each completed source hour is captured after its publication boundary and
stored immutably with raw and metadata SHA-256 links. Source records,
decisions, tick paths, executions, and completed hindsight-oracle dates are
also immutable and hash-linked. Late evidence cannot be backfilled into a
signal.

The same causal rule, costs, risk, clocks, gates, and code are master-locked
before the first source window. The master lock must include every direct
helper and configuration dependency used by the continuous scheduler.

## Admission

Only the pooled two-clock specialist can reach independent review. It requires
at least 12 calendar months, 60 closed trades, 20 trades per clock, and 12
trades per side. It must achieve:

- 45-55% overall win rate;
- realized payoff between 1.35 and 1.75;
- overall PF at least 1.30 and extra-half-pip stressed PF at least 1.15;
- positive net R and PF at least 1.00 at each clock;
- PF at least 1.00 on both long and short trades;
- maximum closed-trade drawdown no more than 15R;
- PF at least 1.00 after removing the best 5% of winners;
- at least 60% positive active months;
- no month above 35% of total positive monthly profit;
- at least 50% same-day/same-side Neutral-oracle precision.

Temporal oracle resemblance is evaluated separately for each clock, preserving
at most one prediction per date for an exact uniform-time-and-side null. Both
clocks must achieve at least 50% precision within 15 minutes, positive lift,
and a one-sided exact-null p-value no greater than 0.025. Requiring both clocks
and using 0.025 controls the two-clock family at 0.05 without choosing a winner.

Passing all gates permits only independent research review. It does not make
the system demo-ready, authorize MT5 attachment, or authorize orders.

## Failure rule

Once the 12-month and sample gates are available, any failed economic,
robustness, clock, direction, monthly, or oracle gate rejects this exact
specialist without historical repair. A successor would need a distinct
causal hypothesis and a new prospective preregistration.
