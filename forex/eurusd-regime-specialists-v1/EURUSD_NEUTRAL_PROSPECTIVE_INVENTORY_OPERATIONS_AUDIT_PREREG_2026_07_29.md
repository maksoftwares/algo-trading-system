# EURUSD Neutral prospective inventory operations audit

Recorded before the first scheduled portfolio operation and with zero strategy
decisions, paths, oracle labels, or operation receipts.

## Purpose

The frozen 00:05 and pooled 06:05/12:05 experts can produce trustworthy
forward evidence only if their scheduled operations actually run on time. This
read-only audit compares immutable JSON-line receipts with the schedules already
defined by the locked component implementations. It does not generate a signal,
download data, replay history, evaluate profitability, or contact a broker.

## Frozen integrity rules

- An operation becomes due five minutes after its scheduled time.
- Dispatch more than 60 seconds late or more than one second early is an
  integrity failure.
- Every due operation must have exactly one matching receipt.
- Malformed stdout, nonempty stderr, duplicate receipts, an outer
  `OPERATION_FAILED_CONTINUING` record, or a late/missed fail-closed result is an
  integrity failure.
- Every operation receipt must state that historical EURUSD P&L was not loaded,
  strategy/signal logic was not changed, and broker action was not allowed.
- The most recent startup receipt for each component must cite the current
  component lock and preserve the no-history/no-broker boundary.
- A startup receipt proves launch, not continuing process liveness. Process
  liveness is checked externally before the first operation; subsequent
  scheduled receipts are the authoritative continuity evidence.
- Missing operations remain missing. The audit never turns a later backfill into
  on-time evidence.

## Interpretation

Before the first due operation, clean startup evidence is reported as
`ARMED_AWAITING_FIRST_OPERATION`. Once receipts are due, a complete clean chain
is `ACCUMULATING_WITH_COMPLETE_OPERATION_RECEIPTS`. Any integrity defect is
`OPERATIONS_INTEGRITY_FAILURE` and blocks research review until independently
adjudicated; it never authorizes retuning.

This audit cannot declare the strategy profitable, cannot make the portfolio
demo-ready, and cannot place or authorize an order.
