# V60 Generic Source-Health Rank Veto V1

Status: retrospective challenger research only.

All historical outcomes through 2026-06-30 and all demo outcomes through
2026-08-24 were exposed before this package was created. This package cannot
authorize deployment.

## Single hypothesis

Use one identical, causal rule for every V60 specialist. For a candidate's own
source, retain the trade unless:

1. At least 20 earlier trades retained by the challenger have closed.
2. That source's latest-20 executed profit factor is below `1.0`.
3. The candidate's pre-existing causal ML rank is below `0.10`.

Missing ranks retain baseline behavior. Each source has an independent health
window. A hypothetically vetoed outcome never enters later health state.

The lookback, break-even health threshold, and bottom-decile rank threshold are
fixed before the full runtime replay. No parameter sweep may nominate a
replacement from this package.

## Required evaluation

Replay the immutable deployed V60 portfolio over 2021-01-01 through 2026-06-30
with unchanged candidates, five-second Dukascopy quotes, broker costs,
concurrency, cooldowns, guardian, and portfolio protection. Require:

- exact baseline identity;
- no worse net P/L, profit factor, closed drawdown, or equity drawdown;
- at least 99% trade retention and 95% frequency retention;
- no negative calendar-year P/L delta;
- no worse final 3-, 6-, or 12-month P/L;
- at least 10 vetoes whose unchanged endpoint cohort has PF below `1.0`.

Even a pass is a historical challenger only. New forward evidence is required
before any broker-action change.
