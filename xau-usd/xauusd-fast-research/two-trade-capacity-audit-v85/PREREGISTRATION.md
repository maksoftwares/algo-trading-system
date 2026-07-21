# V85 Two-Trade Capacity Audit Preregistration

Date: `2026-07-21`

## Question

Can the byte-identical V59/V60 portfolio reach an average of two accepted
trades per weekday in every required modern window merely by admitting the
currently rejected, broker-executable V57 add-on candidates?

## Frozen Inputs

- V59 result, Core, accepted trade ledger, and add-on decision ledger;
- the complete V57 broker-executable add-on candidate ledger; and
- the V60 whole-account floating-equity result.

Every file is SHA-256 bound. The 320 fractional R5 rows rejected by V59 are not
broker-executable at the 0.01 minimum lot and cannot count toward capacity.

## Upper Bound

For each V59 required window, V85 reports:

1. immutable Core trades;
2. currently accepted add-ons and current combined frequency;
3. rejected add-ons by the original V59 decision reason;
4. the mechanical maximum `Core + every distinct V57 candidate`;
5. the integer trade shortfall to a 2.0/day average; and
6. the share of weekdays with at least two entries, descriptively only.

The mechanical maximum is deliberately generous: it ignores position overlap,
concurrent risk, drawdown suspension, daily entry caps, P&L, spread stress, and
margin. It is an impossibility bound, not a portfolio proposal.

## Decision

- If any required window remains below 2.0/day even under the upper bound,
  scheduling-only expansion is ruled out.
- If all windows have enough raw capacity, scheduling remains mechanically
  possible but requires a new preregistered policy and untouched economic and
  shared-account testing.

V85 cannot alter V59/V60, select candidates using outcomes, train a model, or
authorize Python predictions, EA consumption, demo, live, or broker action.
