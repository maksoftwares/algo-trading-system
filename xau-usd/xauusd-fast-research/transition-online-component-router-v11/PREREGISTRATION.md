# Transition Online Component Router V11 Preregistration

## Purpose

Test whether a strictly causal online allocator can turn the four complementary
raw-tick transition components from V9 into an economically eligible transition
specialist. The V9 aggregate result was known before this design, so this is
historical discovery and cannot be an independent confirmation.

## Frozen source

- Exact V9 raw-tick component trades for attempts 23925, 24877, 24995, and 25048.
- Frozen V8 base risk weights: 1.00, 0.25, 0.75, and 0.75 respectively.
- The same shared-position, four-trades-per-UTC-day portfolio rules and the same
  economic gates used by V9.

## Causality rule

For a candidate entering at time `t`, a component's shadow history contains only
trades whose `exit_time < t`. The current outcome, open trades, and all later
outcomes are unavailable. Nonexecuted component trades remain in virtual shadow
history because every component can be observed without placing the trade.

Tests must show that changing a current or future outcome cannot alter any earlier
routing decision.

## Locked search

Exactly 1,000 definitions, attempts 26239 through 27238:

- 200 trailing-mean gates.
- 200 trailing-profit-factor gates.
- 200 Bayesian shrinkage weights.
- 200 cross-component rank gates.
- 200 trailing-drawdown gates.

Definitions are selected by a deterministic SHA-256 ordering over the declared
parameter spaces. Selection cannot inspect trade outcomes. All 1,000 attempts are
included in Benjamini-Hochberg adjustment.

## Eligibility gates

- At least 100 portfolio trades and 15 in every era.
- Stress PF at least 1.10 and average stress R at least 0.02 in every era.
- Total stress PF at least 1.25.
- Closed-trade drawdown no more than 25 R.
- Positive net R after removing the five largest winners.

Economic eligibility does not authorize training or execution. Any survivor still
requires independent replication and prospective shadow evidence. There will be no
same-version tuning after outcomes are opened.

## V10 correction

V10 was invalidated because millisecond exit integers were compared with nanosecond
entry integers, leaving every history snapshot empty. V11 changes no policy range or
economic gate. It explicitly converts both timestamp sides to nanoseconds and adds a
millisecond-precision regression test before sealing a new contract.
