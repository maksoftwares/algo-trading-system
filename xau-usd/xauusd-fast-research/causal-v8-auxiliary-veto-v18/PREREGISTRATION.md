# V8 Auxiliary Veto V18 Preregistration

## Question

Can the frozen auxiliary nonlinear Expected-R score remove a small weak tail
inside `V8_RETEST_HEALTH` while preserving the locked B1+B2+B3 policy
everywhere else?

## Rationale fixed before evaluation

V15-V17 are completed historical experiments. Their out-of-time audits showed
that `aux_expected_r_nonlinear` ranked V8 outcomes above `0.55` AUC in all six
available test folds, with a mean near `0.657`. V18 tests that one relationship.
It does not search families, scores, model classes, directions, or
hyperparameters.

The primary population remains the 3,752-row canonical dataset and its 3,024
mandatory-XAU-feature-pass rows. Auxiliary fitting uses the same
overlap-cleaned 64,319 action labels from 24,835 events in 13,639 structural
episodes. Journey attempts, outcomes, identities, exact timestamps, and
post-trade fields remain excluded from the model surface.

## Frozen policy

For each outer fold:

1. Rebuild the three V15 auxiliary scores using only auxiliary actions whose
   decision and label-end times precede the calibration boundary.
2. Verify byte-level score parity against V15 on the out-of-time test rows.
3. Use only `aux_expected_r_nonlinear` for V8.
4. If fewer than 15 V8 calibration rows exist, preserve B123.
5. Otherwise evaluate only the weighted bottom-tail quantiles 5%, 10%, and 15%
   on V8 calibration rows.
6. A candidate policy may only veto a B123-retained V8 row below its threshold.
   It cannot re-admit a B123 veto, create a trade, or alter another family.
7. Select a threshold only when calibration P&L improves versus B123, at least
   85% of B123-retained V8 weight remains, and mean Expected-R, profit factor,
   and drawdown do not worsen.
8. Missing scores, insufficient support, or no eligible threshold preserve
   B123.

## Historical gate

V18 passes only if exact V60 replay:

- improves all-history P&L versus both raw V60 and locked B123;
- is nonnegative versus raw V60 in the latest three months;
- improves raw V60 over six and twelve months;
- retains at least 95% of raw trades;
- does not worsen all-history profit factor or closed-trade drawdown.

Historical outcomes and the family-level AUC audit were exposed before V18 was
designed. Even a pass only nominates a prospective challenger. V14 remains the
only locked prospective ML lane. V18 has no Python-serving, shadow, EA, demo,
live, sizing, runtime, or broker authority.
