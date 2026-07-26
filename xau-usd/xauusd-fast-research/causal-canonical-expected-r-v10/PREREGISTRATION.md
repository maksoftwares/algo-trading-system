# Canonical Expected-R V10 Preregistration

V10 is a development-only experiment on already-exposed canonical outcomes.
Its purpose is to determine whether partial pooling can preserve approximately
one candidate per weekday while improving stressed expected R in every annual
test fold, including July 2025 through June 2026.

The model is fixed before the formal artifact run:

1. Use only canonical rows with `xau_feature_status == PASS` and the frozen
   Step 3 purged chronological assignments.
2. Use the numeric columns in frozen feature blocks B1 and B2 plus `family_id`.
   No outcome, historical decision, exact timestamp, candidate identity, COMEX,
   journey archive, or demo outcome enters the predictors.
3. Fit Ridge regression to stressed net R clipped to [-3R, +3R], using
   structural weights, alpha 300, and no recency weighting.
4. The design matrix contains standardized global numeric effects, one family
   intercept per specialist, and family-by-numeric deviations scaled by 0.25.
   Ridge shrinkage makes the family deviations partial rather than independent.
5. In each outer fold, select the weighted 70th percentile and above. A family
   receives its own calibration-only threshold with at least eight calibration
   rows; otherwise it uses the pooled calibration threshold.
6. Test outcomes cannot alter the model, threshold, family fallback, or gates.
7. Evaluate six purged tests, pooled economics, family attribution, and 5,000
   UTC-week block bootstrap resamples.

Every registered gate is required. A historical pass still means only that a
working offline research model exists. Because the development campaign has
already observed these historical outcomes, it requires new prospective
evidence before any runtime role can be considered.

