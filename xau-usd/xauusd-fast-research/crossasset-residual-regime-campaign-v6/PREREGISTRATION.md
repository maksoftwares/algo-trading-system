# Cross-Asset Residual Regime Campaign V6

## Objective

Test 1,000 mechanically distinct definitions that use causal gold dislocations
from the US dollar and US Treasury total-return series. Five mechanism families
belong to CHOP and five belong to TRANSITION. This is a new mechanism class,
not a parameter repair of a previous outcome.

## Attempt ledger

- Attempts: `24120` through `25119`, inclusive
- CHOP: 500 definitions
- TRANSITION: 500 definitions
- Five mechanics per owner
- 100 coverage-eligible definitions per mechanic

Definitions are sorted by a SHA-256 hash of owner, mechanic, and canonical
parameters. Historical signal coverage may admit a definition. P&L, exits, and
labels may not influence manifest membership.

## Causal residual

At each M15 decision close, dollar and bond pressures are converted to the
direction expected to support gold and averaged. A rolling beta from macro
consensus to gold return is estimated using observations strictly before the
decision timestamp. The current gold residual is then standardized using only
prior residuals. Future rows cannot alter an earlier feature value.

Feature keys combine H1, H4, or H12 return horizons with prior two-day or
ten-day scale windows. Rolling betas are clipped only for numerical stability.

## Mechanisms

CHOP tests residual fading, residual re-entry, macro lag catch-up, dollar/bond
disagreement fading, and beta-conditioned overshoot fading.

TRANSITION tests ancestry reacceleration, macro lag catch-up, residual breakout,
single-factor resolution, and ancestry overshoot reversal.

Shock remains an abstain state. Every transition definition is restricted to
the frozen `TRANSITION_UNKNOWN` state and every chop definition to frozen
`CHOP` decisions.

## Execution and gates

Entries occur at the next complete M15 bar open using executable bid/ask prices.
Stops, targets, same-bar stop-first ordering, ticket cost, holding cost, stress
slippage, non-overlap, and the daily cap are inherited unchanged from the macro
regime routing campaign.

All original economic gates remain unchanged. A historical pass is discovery
evidence only and requires a separately locked exact raw-tick confirmation,
independent-period evidence, and prospective shadow observation.

Same-version post-outcome tuning, paid data, Databento, model training, and
trading authorization are prohibited.

