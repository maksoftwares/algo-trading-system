# A1 XAUUSD H4 Cluster High-Water Total-MTM V3 Addendum

Date: 2026-07-11
Boundary: settlement-sequencing implementation repair in development Strategy Tester
only; no broker action is authorized.

## Why V3 is required

The realization-invariant rule was preregistered as cumulative realized primary P/L
plus current primary floating P/L.  The first transaction-accumulator implementation
completed exact MT5 but its ledger showed hedge trigger and release pairs at the same
primary TP timestamp.  MT5 can expose the changed position cohort to `OnTick` before
the primary deal accumulator is updated in `OnTradeTransaction`.  That temporarily
recreated the same false floating-P/L drawdown the rule was designed to remove.

That V2 implementation result is retained as an implementation failure:

| Horizon | Net USD | PF | Native relative equity DD |
| --- | ---: | ---: | ---: |
| five-year | 845.89 | 1.0639 | 33.94% |
| ten-year | 3,707.19 | 1.2503 | 23.77% |

It is not treated as the economic test of total MTM.

## Locked sequencing correction

V3 changes no strategy, trigger, release, size, stop, or target input.  It keeps the
5.00% trigger and 2.00% release.  When primary volume changes or a primary deal is
reported, it:

1. synchronizes cumulative primary profit, commission, swap, and fee from MT5 deal
   history;
2. recomputes cluster total MTM as realized since cluster start plus current floating;
3. defers hedge action for that settlement tick;
4. permits hedge decisions on the following tick from the synchronized state.

Successful release rearms directly without rebasing the high-water mark.  Cluster
state resets only after the final primary is flat and any hedge has closed.  H4
outcomes, loss dates, and future values are absent.

## Acceptance and stopping rule

The prior acceptance gates remain: ten-year net at least USD 7,000, native relative
equity drawdown at most 12%, PF at least 1.30, all 307 primary entries, and zero
failures/unreconciled volume.  Five years must retain all 156 entries, PF at least
1.30, and clean reconciliation.  Both results are disclosed.

This is the final mechanical high-water implementation test.  Failure closes this
lane and moves development to the preregistered independent R5 specialist; it does
not authorize another hedge parameter or state-machine variant.

## Exact result

Status: `H4_CLUSTER_HIGHWATER_TOTAL_MTM_V3_FAILED`

| Horizon | Primary entries | Hedge entries | Net USD | PF | Native relative equity DD | Failures |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| five-year | 156 | 223 | 2,277.89 | 1.1958 | 25.40% | 0 |
| ten-year | 307 | 177 | 3,722.21 | 1.2511 | 23.68% | 0 |

Both runs had 98% history quality, retained every original primary entry, reconciled
all position and hedge volume, and finished flat.  The corrected state machine did
not approach either the profit or drawdown gate.  Per the stopping rule, the
mechanical high-water lane is closed.
