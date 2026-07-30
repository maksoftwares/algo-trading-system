# EURUSD forward residual live-signal protocol

## Purpose

The residual-regime evaluator resolves both sides only after the six-hour path
is complete. That is valid forward research, but it cannot prove that a signal
was available at the intended 20:00 UTC entry clock.

This publisher closes that deployment gap. It emits one immutable decision
before the outcome exists, using the exact frozen residual strategy, only prior
resolved training outcomes, and only feature rows available at publication.
It has no order path.

## Publication boundary

The decision clock is 20:00 UTC. Publication is allowed from 20:01 through
20:10 UTC on a forward-floor weekday.

- Before the clock, nothing is written.
- If required context is missing inside the window, immutable cash is written.
- If the publisher starts after the deadline, immutable missed-deadline cash is
  written.
- A cash decision cannot later be replaced with a signal.
- Manual as-of clocks and historical backfill are prohibited.

The 20:00 residual clock is later than both upstream opportunity sources:

- frozen M15 signals can occur only from 06:00 through 09:45 UTC; and
- the frozen daily learner decides at 08:00 UTC and resolves before its 14:10
  UTC operations cycle.

Same-date residual ownership is therefore known before publication without
future information.

## Information set

The publisher:

- loads only prospective rows at or after the August evidence floor;
- computes the frozen cross-pair context from completed M5 intervals ending at
  19:55 UTC;
- reconstructs each regime-side history only from prior append-only residual
  records with fully resolved outcomes;
- refuses any current-date or future outcome in its training input;
- applies the unchanged global warm-up, same-regime sample, shrunk expectancy,
  PF, stressed PF, and recent PF gates; and
- publishes no outcome, target hit, stop hit, or future price field.

## Evidence and parity

Each record contains the decision clock, actual publication clock, causal
context, regime, training count, pre-decision statistics, selected side or
cash reason, and an explicit false order authorization.

After the outcome window, an independent parity step must compare the immutable
published decision with the research adjudicator's reconstructed decision and
outcome. Only exact live-published signals may enter the eventual executable
combined portfolio.

## Prohibitions

No pre-floor decision, backfill, manual as-of override, post-outcome
publication, late signal recovery, imputation, strategy change, or order is
allowed.
