# Action Models V3 Preregistration

This model and evaluation contract is frozen before any V3 model is fitted or
any V3 test prediction is produced.

## Question

Can a small, mechanism-specific model use the 58 locked causal features to pick
one available stop/target action and reject weak events while preserving the
total edge and frequency of a strong deterministic fixed-action benchmark?

## Disjoint Lanes

Every event has one outcome-blind owner. Ownership priority is downside
impulse/retest, then opening-range reversal, then break-and-run. This creates
three disjoint lanes and prevents a confluence event from appearing as
independent evidence in several family models.

`UNSAFE_SHOCK` remains a mandatory abstain state and does not enter fit,
calibration, or test policy populations. Missing actions are not imputed. The
model may rank only actions that passed the original causal entry-gap, risk, and
spread checks and therefore have a resolved stressed label.

## Models

Each lane and fold fits exactly two fixed regressors:

1. standardized ridge regression;
2. regularized histogram gradient boosting regression.

The fit target is stressed net R clipped to the frozen range [-3.0R, 2.5R].
All economic evaluation uses the original unclipped stressed result. Training
uses the V3 structural action weights, which total one per 30-minute episode.
No hyperparameter search is permitted.

## Calibration Policy

Each lane/fold must have at least 650 eligible fit action rows. This floor is
below the smallest causally eligible disjoint-lane fit population (674 rows in
BREAK_AND_RUN F2021) and is fixed before any calibration or test outcome is
examined.

For every event, each model ranks the causally available actions and keeps the
highest score, with fast, intraday, then swing as the outcome-blind tie order.
Three score thresholds retain approximately 100%, 80%, or 60% of calibration
events. A policy is eligible only if it clears every frozen calibration gate.
The deterministic ranking key is highest weighted R sum minus 0.10 times
drawdown, then higher coverage, the declared model order, and the declared
retention order.

The benchmark ranks the three fixed actions by calibration mean stressed R
minus one standard error. At each event it takes the first available action in
that frozen ranking. Thus it trades every event without receiving impossible
actions or hindsight from the test partition.

If no policy clears calibration, the best diagnostic policy is still evaluated
once, but the fold and family must fail closed.

## Test And Acceptance

The six V3 July-to-July test partitions are disjoint. No test outcome can select
a model, threshold, action ranking, or lane. Results are aggregated only after
all fold choices are fixed.

Acceptance requires positive cost-stressed expectancy, profit factor, minimum
coverage and raw opportunity frequency, controlled event-sequence drawdown,
four positive folds, a positive latest fold, predictive rank signal, positive
confidence bounds for selected expectancy and common-event action uplift, and
non-inferior total episode return versus the take-all benchmark. Five-thousand
fixed-seed weekly block bootstrap resamples supply the economic intervals.

All history is previously exposed development history. A passing lane is only a
candidate for a later prospective confirmation design.

## Authority

Model fitting and threshold fitting are authorized only inside this offline
package. Portfolio simulation, Python serving, ML shadow, EA consumption,
demo/live trading, sizing changes, terminal changes, and broker action remain
forbidden regardless of the result.
