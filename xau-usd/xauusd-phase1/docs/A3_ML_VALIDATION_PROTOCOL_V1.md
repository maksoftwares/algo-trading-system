# A3 ML Validation Protocol V1

Status: PRELOCK_CONTRACT

This contract owns outer/inner folds, purge, embargo, calibration split, holdout, long/short OOS diagnostics, fold diagnostics, forward evidence rules, and parity expectations.

## No Random Splits

Never use:

- random train/test split;
- shuffled KFold;
- shuffled StratifiedKFold;
- random row sampling.

## Walk-Forward Structure

Use:

- 5 outer expanding folds;
- 3 inner expanding folds.

Each sample has:

- event_start;
- event_end;
- setup_group_id.

For each outer fold:

1. chronological training occurs before the test block;
2. remove event-interval overlap;
3. apply embargo;
4. keep setup_group_id intact;
5. fit transformations on training only;
6. reserve disjoint chronological calibration tail;
7. select threshold on calibration only;
8. evaluate once on outer test.

Embargo is max(full label horizon, one M5 bar). The implementation must support active-market time for the 288-bar horizon.

Final forward data must be inaccessible to training code.

## Fold Diagnostics

Validation reports must include the per-fold purge, embargo, calibration, class-count, and feature-budget diagnostics owned by A3_ML_DATA_CONTRACT_V1.md and A3_ML_FEATURE_BUDGET_CONTRACT_V1.md.

## Direction Diagnostics

Every outer fold must report LONG and SHORT diagnostics from untouched outer-test predictions as defined in A3_ML_DIRECTION_ASYMMETRY_PROTOCOL_V1.md.

These diagnostics are reporting only and cannot select the same fold's model.

## Calibration Isolation

Calibration rows do not appear in model-fit training rows.

Threshold selection code must not access outer-test labels.

## Forward Evidence

Forward checkpoint minimum:

- 100 retained virtual trades;
- 20 active days;
- 4 calendar weeks;
- 25 long;
- 25 short.

Possible checkpoint states:

- FORWARD_FAIL;
- FORWARD_CONTINUE;
- FORWARD_CHECKPOINT_OK.

This checkpoint cannot authorize deployment.

Forward confirmation minimum:

- 300 retained virtual trades;
- 12 active market weeks;
- RISING and FALLING regimes;
- at least 8 weeks with at least 10 retained trades;
- adequate MDE/power.

No deadline may relax gates.

## Export And MQL Parity Expectations

Before any execution discussion, Python/MQL feature parity and export parity must pass. Passive MQL5 work is not part of C00 and must not include broker action.
