# V57 Auxiliary Calibrator V17

V17 tests whether the three frozen V15 auxiliary scores should be interpreted
by a dedicated V57 Expected-R calibrator rather than a pooled global policy.

Only `V57_BREAK_SWING_H4ADX_HIGH` decisions may differ from locked B123:

- a B123-retained V57 candidate is always retained;
- a B123-vetoed V57 candidate remains vetoed only when the dedicated V57 score
  is below its calibration-only threshold;
- V57 retains all candidates when its own fit/calibration support is
  insufficient or no calibration edge passes the frozen constraints;
- every non-V57 candidate keeps its locked B123 decision.

The lane is historical research only. It does not modify V14, V15, V16, MT5,
the demo EAs, or any runtime authorization.
