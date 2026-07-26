# Profit Policy V12 Preregistration

V12 keeps the frozen V10 expected-R models and causal feature surface unchanged.
Only the selection policy changes.

For each available outer fold, V12 scores that fold's earlier calibration rows
with the already-fitted V10 model. It searches the locked pooled weighted-score
quantile grid and selects the cutoff with the highest calibration stressed,
normalized 0.01-lot USD sum.
The candidate cutoff must not reduce calibration mean R, profit factor, or
episode-level drawdown, and it must retain at least 20% of structural weight.

The zero quantile retains all candidates and is the mandatory fallback. A
nonzero cutoff must improve calibration normalized USD by at least $10. Folds
with fewer than 1,000 fit rows retain all candidates.

The primary historical gate is total out-of-time stressed normalized USD above
both the non-ML baseline and V11. This experiment is post-outcome research because prior
historical results have already been observed. A pass therefore requires new
forward confirmation and cannot authorize shadow, demo, or live use.
