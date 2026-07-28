# EURUSD Neutral prospective campaign orchestration V1.2 preregistration

Date: `2026-07-28`

Status: `FROZEN_BEFORE_PROSPECTIVE_START_AND_FIRST_SIGNAL`

V1.2 supersedes the immutable V1.1 orchestration lock
`a54e1fd7ee0ae664adfa8fee7bd18b575f622bc8fa2d3efb248174903d55bfa1`.
At the V1.2 freeze there were zero linked-actual manifests, event-market
manifests, ownership records, signal records, terminal trade records, and
oracle manifests.

The EURUSD Neutral strategy is unchanged. V1.2 does not change its event
families, side rule, three-way agreement, entry, stop, 1.5R target, 12-hour
hold, costs, one-position rule, frequency policy, or prospective admission
gates. It loads no historical P&L and performs no parameter search.

## Defect corrected

V1.1 hash-validated every evidence file, but its non-oracle loaders did not
apply the command's `--as-of` timestamp. If later evidence already existed on
disk, an earlier chronological replay could see:

- a linked actual before its recorded observation time;
- an event-market feature before its capture time;
- an ownership record before its observation time; or
- a complete trade path before its safe path-capture time.

Oracle labels already had an explicit safe-known-time filter. V1.2 applies the
same point-in-time principle to every other evidence stage and to immutable
ledger records.

## Frozen point-in-time visibility

All evidence files and manifests remain hash-validated fail-closed, including
files whose timestamps are later than the requested replay time. After
validation, decision-visible rows must satisfy:

- forecast observation time no later than `as_of`;
- linked-actual observation time no later than `as_of`;
- event-market observation time no later than `as_of`;
- ownership observation time no later than `as_of`; and
- trade-path observation time no later than `as_of`.

Inventory counts record all validated artifacts. Decision counts record only
artifacts known by `as_of`.

The campaign selects the earliest admissible actual, earliest complete market
capture, and earliest valid ownership record from the visible set. Later
contradictory revisions remain in the evidence inventory but cannot replace an
immutable signal or terminal trade.

## Immutable-ledger replay

A point-in-time replay may run after later signal and trade records have
already been persisted. Those records are still hash-validated, but they are
excluded from the earlier ledger view until their own safe known time:

- a signal becomes visible when all of its decision evidence is known;
- a cash or position-skip terminal record becomes visible by its entry time;
- a closed trade becomes visible when its complete path was observed; and
- a legacy closed record without that field uses the conservative
  `entry + 12 hours + 60 seconds` boundary.

Ledger inventory hashes therefore exclude records not yet visible at the
requested replay time. No record is deleted, rewritten, or backdated.

## Frozen rehearsal

The integration rehearsal materializes every evidence stage in advance and
then replays five chronological boundaries:

1. before the actual is observed;
2. after the actual but before the market capture;
3. after the signal evidence but before the path;
4. one second before the path is known; and
5. exactly when the path becomes known.

Expected states are respectively no actual, missing market, pending path,
pending path, and one closed trade. The rehearsal repeats the earlier views
after the future signal and trade records have been persisted.

The separate revision-invariance rehearsal also appends a later actual and
market capture that both reverse the original LONG evidence to SHORT. The
evidence and process hashes must change, while the immutable signal and trade
bytes must not.

All processing remains local, research-only, network-free, and unable to place
demo or live broker orders.
