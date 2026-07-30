# EURUSD residual live-outcome and selection-parity protocol

## Purpose

Only the actual bid/ask captured by the read-only MT5 bridge can support
execution P&L. The research evaluator's earlier 20:00 entry is not substituted.

This adjudicator preserves raw Capital.com ticks from the captured entry,
resolves the exact 8/12-pip and six-hour path, and independently compares the
pre-outcome published selection with the later terminal research decision.

It has no order path.

## Entry-tick identity

The bridge currently preserves tick time to one second plus the exact bid and
ask. The adjudicator queries the one-second entry window and requires exactly
one tick matching both prices. Zero or multiple matches are an invalid outcome;
the entry is never guessed.

Raw ticks are sorted, canonicalized, SHA-256 hashed, and stored immutably. No
missing tick is filled or inferred.

## Execution

- LONG enters at the captured ask and exits on bid.
- SHORT enters at the captured bid and exits on ask.
- Stop distance is eight pips.
- Target distance is 12 pips.
- Stop is checked before target.
- A stop gap uses the first executable quote.
- A target uses the target price.
- Time exit uses the last tick no more than 60 seconds before six hours.
- Additional stress subtracts 0.5 pip per trade.
- P&L uses 0.01 lot and USD 10 per pip per standard lot.

Friday 20:00 UTC receipts are non-evaluable cash because the six-hour path
crosses the weekly market close. They are never counted as live outcomes or
future demo entries.

The publisher now writes Friday market-closure cash before side selection. Its
parity record is self-terminal because no six-hour research outcome can exist
across the weekly close. This operational mapping is not an economic trade and
does not count toward the 50-outcome gate.

## Selection parity

For each terminal research decision, the adjudicator compares the immutable
pre-outcome record's decision time, regime, side, reason, training count,
context, and regime-side statistics. Upstream-owned and missing-context cash
states have their own exact mappings.

Operational missed-deadline cash is not converted into a strategy signal.
Friday market-closure cash is terminal without waiting for a nonexistent
research path.

## Admission

At least 50 matched decisions and 50 live executable outcomes are required,
with:

- zero selection mismatches;
- zero invalid outcomes;
- 45-60% wins;
- payoff at least 1.25;
- PF at least 1.15;
- stressed PF at least 1.05;
- best-5%-removed PF at least 1.00;
- both chronological halves above PF 1.00; and
- positive net P&L.

MT5 ordering parity and disarmed shadow soak remain separate mandatory gates.
The adjudicator always reports `demo_order_authorized=false`.
