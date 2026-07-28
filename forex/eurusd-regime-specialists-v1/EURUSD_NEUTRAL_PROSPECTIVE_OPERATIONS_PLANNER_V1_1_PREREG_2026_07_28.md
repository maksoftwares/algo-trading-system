# EURUSD Neutral prospective operations planner V1.1 preregistration

Date: `2026-07-28`

Status: `FROZEN_BEFORE_PROSPECTIVE_START_AND_FIRST_SIGNAL`

V1.1 supersedes only the command launcher in the immutable V1 operations
planner. The V1 planner emitted commands beginning with `python`, but the
current Windows host resolves that name to a nonfunctional Microsoft Store
stub. The documented repository runtime is `uv`, and an unmodified V1 command
therefore cannot execute on this host.

The V1 planner source remains byte-for-byte unchanged. V1.1 wraps it with a
new locked configuration whose commands begin with:

`uv run --offline --with pandas --with numpy --with pyarrow --with scikit-learn python`

`--offline` prevents dependency resolution from making an unrecorded network
request. The capture command itself may still make only the network request
already allowed by its immutable evidence contract.

## Invariants preserved

V1.1 does not change:

- event families, event identities, signal direction, or agreement logic;
- forecast polling cadence or any safe evidence timestamp;
- Regime 1 Neutral ownership;
- entry, stop, target, holding period, costs, sizing, or one-position routing;
- append-only evidence selection or point-in-time visibility;
- validation, falsification, oracle, profitability, or drawdown gates; or
- research-only and no-broker restrictions.

At this freeze there are zero actual, event-market, ownership, signal,
terminal-trade, and oracle rows. The ownership prewarm cache contains 6,085
hash-validated symbol-hours, with zero gaps among safely completed hours. No
historical P&L was loaded.

The old V1 planner and its lock remain intact for audit. New operations use
`plan_prospective_neutral_operations_v1_1.py`.
