# V57 Auxiliary Calibrator V17 Preregistration

## Question

Can the auxiliary evidence improve V57 veto decisions when it is calibrated
inside that specialist, without changing any other specialist?

## Frozen evidence

V14 remains the immutable prospective lane. V15 and V16 remain completed
historical experiments. V17 uses the same overlap-cleaned auxiliary population
and the same three causal auxiliary scores. Journey-attempt rows, identity
features, outcomes, exact timestamps, and post-trade features remain excluded
from the model surface.

The specialist is fixed before evaluation:
`V57_BREAK_SWING_H4ADX_HIGH`.

## Model and policy

For every outer fold:

1. fit the three V15 auxiliary models only on actions whose decision and label
   end precede the canonical calibration boundary;
2. score canonical V57 FIT, CALIBRATION, and TEST rows;
3. when V57 has at least 150 FIT rows and 25 CALIBRATION rows, fit one Ridge
   Expected-R model on only the three auxiliary scores, using fit-only median
   imputation, standardization, structural weights, target clipping to
   `[-3R, 3R]`, and fixed alpha `50`;
4. calculate only the weighted 10%, 15%, and 20% V57 calibration thresholds;
5. always retain B123-retained V57 candidates;
6. retain a B123-vetoed V57 candidate only when its dedicated score is at or
   above the selected threshold;
7. choose the threshold using V57 calibration economics only, requiring at
   least 85% V57 weight retention, positive P&L improvement versus raw V57,
   and non-worse mean Expected-R, profit factor, and drawdown;
8. retain all V57 candidates when support is insufficient or no threshold is
   eligible;
9. preserve the exact locked B123 decision for every non-V57 candidate.

No specialist identities other than the fixed V57 scope enter the model. No
family interactions, direction branches, recency weights, hyperparameter
search, or post-result threshold changes are permitted.

## Decision

V17 passes its historical gate only if exact V60 replay:

- improves all-history net P&L versus both raw V60 and locked B123;
- is nonnegative versus raw V60 in the latest three months;
- improves raw V60 over six and twelve months;
- retains at least 95% of raw trades;
- does not worsen all-history profit factor or closed-trade drawdown.

Historical outcomes were exposed before this design. A pass would nominate a
prospective challenger only. It would not authorize Python serving, shadowing,
EA consumption, demo trading, live trading, sizing, or broker actions.
