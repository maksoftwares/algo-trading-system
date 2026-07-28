# EURUSD Neutral prospective execution V2.1 preregistration

Date: `2026-07-28`

Status: `FROZEN_BEFORE_PROSPECTIVE_START_AND_FIRST_ELIGIBLE_SIGNAL`

This operational amendment replaces V1 and the original V2 contract before
any eligible prospective signal, trade, or outcome exists. V1 correctly froze
the macro, EURUSD, DXY,
and Treasury agreement rule, but its named entry was the M5 open at which the
third observation bar completed. The immutable public Dukascopy evidence is
not admissible until at least 60 seconds later. Executing at the earlier open
would therefore use information that had not yet been captured.

V2.1 preserves the owned families, Neutral gate, three-way directional rule,
4–25-pip structural risk, 1.5R target, 12-hour hold, fixed 0.01-lot reporting
size, and every admission threshold. It makes one causal correction:

- entry is the first M5 open strictly after the forecast, actual, completed
  three-bar market reaction, and Neutral-ownership evidence are all observed.

The entry bar remains excluded from confirmation. The Neutral state uses the
latest common completed five-market H1 classifier row no later than the prior
date's 23:00 cutoff. This is the frozen historical parent's backward-as-of
selection rule; it does not forward-fill or impose a tolerance, and the
selected state's staleness is recorded. Ownership evidence may be archived
after midnight, but must exist before entry and cannot use any event-day
post-midnight classifier bar.

## Frozen execution semantics

- Long entry uses the effective ask open; short entry uses the effective bid
  open.
- Enforce at least 0.7 pip spread and 0.1 pip adverse slippage per side.
- The structural stop is the three-bar EURUSD midpoint extreme plus a
  0.5-pip buffer.
- Risk distance is clamped to 4–25 pips. This resolves the word “capped” before
  any prospective outcome.
- Target is 1.5 times initial risk.
- Same-M5 stop/target ambiguity is a stop.
- Missing M5 bars leave the outcome pending; they are never silently skipped.
- Maximum hold exits at the close of the final complete M5 bar before the
  12-hour deadline.
- Only one position may be open. A later signal remains blocked while an
  earlier outcome is incomplete.
- When append-only captures contain revisions, use the latest admissible
  pre-release forecast but the earliest admissible linked actual, complete
  market reaction, and valid Neutral-ownership capture. Later revisions never
  replace the evidence selected for a signal.

No frequency requirement exists. Promotion cannot be reviewed before 30
closed trades and 12 calendar months, and all economic, side-balance,
cost-stress, winner-removal, drawdown, and same-day/same-side Neutral-oracle
precision gates must pass. Passing triggers research review only and never
automatically enables broker orders.

No historical P&L may be loaded for V2.1. The first valid evidence date remains
`2026-07-29T00:00:00Z`.
