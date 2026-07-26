# Loss-Signature One-Class V1 Preregistration

This is an exposed-history, research-only experiment requested by the owner.
It asks one narrow question: can a model fitted exclusively on losing trades
identify a loss-enriched region in later chronological test years?

The corrected Expanded Dataset V4 is the only population. It contains 73,116
resolved action rows, including 42,067 stressed failures, 58 finite causal
features, structural weights, and six purged July-to-July folds. The canonical
benchmark and quarantined journey archive do not enter this experiment.

For every fold:

1. Use only eligible FIT rows whose stressed outcome is nonpositive.
2. Fit one deterministic Isolation Forest. No winning FIT or CALIBRATION row
   may enter fitting, imputation, scaling, feature selection, or thresholding.
3. Define loss similarity as the estimator's `score_samples` output, where a
   larger value means more similar to the fitted loss population.
4. Set the primary veto threshold to the weighted 80th percentile of FIT-loss
   scores. This flags the most loss-like 20% of the historical loss
   distribution. Quantiles 0.60, 0.70, and 0.90 are diagnostics only and cannot
   replace the primary after test outcomes are opened.
5. Evaluate once on the fold's untouched TEST rows. Winners are used only for
   evaluation of loss precision, winner collateral, AUC, and economics.

The primary experiment requires all registered gates: pooled weighted loss AUC
at least 0.55, at least 0.05 absolute loss-precision lift, positive 95%
bootstrap lower bounds for both precision lift and retained-EV lift, at least
10% loss recall, at least 75% retained coverage, at least 0.03R retained-EV
improvement, improved retained profit factor, positive precision and EV lift
in at least four folds, and positive precision and EV lift in F2026.

Passing would mean research progress only. It would not authorize serving,
shadowing, filtering, MT5 attachment, demo/live execution, sizing, or broker
action. Failure retires this exact one-class loss-signature specification.

