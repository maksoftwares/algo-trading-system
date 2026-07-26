# Exploratory Analysis Contract

## Purpose

Identify entry-time measurements that may distinguish winning and losing
trades within a specialist. The package is diagnostic only. It does not train
an executable model or select a trading threshold.

## Evidence Boundary

All labels through 2026-06-30 were exposed before this package was designed.
No result from this analysis can authorize shadow, demo, live, EA, sizing,
portfolio, or broker action.

The canonical population includes historically accepted and rejected
candidates. Historical acceptance is used only to reconcile the V59 core and
add-on cohorts. It is never a predictor or an outcome label.

## Matched Comparison

One representative is retained per family, direction, and structural episode.
Winners and losers are matched without replacement inside exact strata:

- specialist family;
- direction;
- calendar year;
- UTC session;
- stop mode;
- target mode.

Within each stratum, pairs are chosen by the smallest absolute decision-time
distance. The matching procedure does not read feature values.

## Walk-Forward Transfer

For each family and feature:

1. determine whether larger or smaller values favored winners using only the
   fold's fit partition;
2. standardize using only fit-partition location and scale;
3. score the untouched test partition once;
4. aggregate only disjoint test rows.

No test outcome may choose the feature direction, scale, family, threshold, or
gate.

## Lead Gate

A stable exploratory lead requires sufficient family rows, both target
classes, matched pairs, a material descriptive effect, a matched-pair
bootstrap interval that excludes zero in the same direction, at least two
eligible walk-forward folds, positive transfer in most folds, acceptable
latest-fold behavior, and an aggregate signed-feature AUC above the locked
minimum.

Failure means only that the tested feature did not provide stable univariate
separation. Passing creates a prospective research hypothesis, not a trading
model.

## Prohibitions

- no COMEX features;
- no candidate IDs, timestamps, historical decisions, outcomes, MFE, MAE, or
  exits as predictors;
- no same-version post-result gate changes;
- no model fitting beyond the signed univariate transfer diagnostic;
- no runtime or broker integration;
- no Databento access or new data acquisition.
