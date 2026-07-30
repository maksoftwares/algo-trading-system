# EURUSD annual expanding-cell specialist preregistration

Date: 2026-07-30

Status: **FROZEN_BEFORE_RESULT**

Demo-order authorization: **false**

## Hypothesis

The archived RSI/Bollinger opportunity families may drift across regime,
seed, and UTC-hour cells. A cell that has accumulated enough completed
positive-expectancy evidence may remain useful for the following calendar
year even though a single selection frozen through 2024 failed to transfer
cleanly into 2025-2026.

## Causal contract

At 00:00 UTC on January 1, group all opportunity outcomes whose exits
completed before that instant by:

- causal owner/regime;
- fixed seed/rule identifier;
- entry hour UTC.

Select a cell only when its completed history contains at least 15 trades,
45%-65% wins, and profit factor at least 1.30. Hold the selected cell list
unchanged for the entire following calendar year. Refit only at the next
January boundary.

The execution contract retains the archive's chronological priority,
one-open-position rule, and 24-trade daily ceiling. No current-year outcomes
can change a current-year decision.

## Evidence boundary

Development consists only of 2022 and 2023, with a separate January-boundary
refit for each year. The locked 2024, 2025, and 2026H1 windows remain
unscored unless every development admission gate passes.

The development candidate must produce at least 50 trades and 0.08
trades/weekday, PF at least 1.15, stressed PF at least 1.05, PF above 1.00 in
both development years, best-5%-removed PF at least 1.00, and drawdown no
greater than 15R.

Locked validation, if opened, requires at least 80 trades, 0.08
trades/weekday, PF at least 1.15, stressed PF at least 1.10, PF above 1.00 in
every validation window, latest-12-month PF at least 1.10,
best-5%-removed PF at least 1.00, drawdown no greater than 15R, and useful
date independence from the protected M15 sleeve.

## Non-negotiable decision rule

There is one cell definition and one threshold set. No post-result threshold,
window, cell-dimension, side, seed, hour, or gate rescue is allowed. Even a
historical pass remains research-only because the wider archive is not
pristine; fresh prospective confirmation is required before demo orders.
