# V19 Replacement-Capacity Mechanism Audit

## Purpose

This audit exercises the locked V19 implementation end to end before clean
forward candidates arrive. It is a deterministic mechanism test, not an
economic backtest and not evidence that Dynamic V6 is profitable.

The audit imports the exact V19 package locked under contract
`fdabc9e2997592b06568bb5e405154abdb3888b921a61d70620e06bde2cb4905` and
the frozen replay, evaluator, V6 scenario, V60 configuration, and protection
overlay identified by that contract.

## Fixed fixture

1. Use the real `V57_BREAK_SWING_H4ADX_HIGH` source limits, including its
   one-position source cap.
2. Seed a synthetic, explicitly degraded 50-trade source history. This seed is
   only a mechanism fixture and cannot enter prospective evidence.
3. Candidate `FIXTURE_INFERIOR_OCCUPANT` enters first, has rank `0.05`, and
   loses `$10.30` if accepted.
4. Candidate `FIXTURE_BETTER_REPLACEMENT` arrives five minutes later, has rank
   `0.50`, and wins `$19.70` if accepted.
5. Candidate lifecycles overlap. Baseline V60 must accept the first candidate
   and reject the second because the V57 source slot is occupied.
6. Frozen Dynamic V6 must veto the first candidate and accept the second using
   the newly free slot.

## Required result

- V60 accepted IDs: only `FIXTURE_INFERIOR_OCCUPANT`.
- V6 accepted IDs: only `FIXTURE_BETTER_REPLACEMENT`.
- V6 veto IDs: only `FIXTURE_INFERIOR_OCCUPANT`.
- V6 replacement-accept IDs: only `FIXTURE_BETTER_REPLACEMENT`.
- Both twins finish flat.
- V60 fixture P/L: `-$10.30`.
- V6 fixture P/L: `+$19.70`.
- No MetaTrader5 import, order call, runtime change, or deployment authority.

Any mismatch is `MECHANISM_PARITY_FAIL`. A pass only proves that V19 can
represent replacement capacity correctly. It cannot authorize deployment.
