# A3 ML Model Selection Protocol V1

Status: PRELOCK_CONTRACT

This contract owns model families, hyperparameter grids, calibration, thresholding, final gates, symmetric-versus-interaction selection, and deterministic benchmark comparison.

## Eligible Models

M0_BASE_RATE:

- constant probability = training-fold positive rate.

M1_LOGISTIC_L2_SYMMETRIC:

- allowed training-only imputation;
- StandardScaler;
- LogisticRegression penalty=L2;
- C grid: 0.01, 0.10, 1.00;
- no class_weight="balanced".

M1_LOGISTIC_L2_DIRINT:

- conditionally eligible only under A3_ML_DIRECTION_ASYMMETRY_PROTOCOL_V1.md;
- same C grid and selection process as symmetric logistic.

M1_LOGISTIC_L1_DIAGNOSTIC:

- only when minority events >= 300 and budget >= 10;
- C grid: 0.01, 0.10;
- diagnostic only in V1.

M2_HIST_GB:

- only at MATURE_MODEL;
- never selected before logistic and deterministic comparisons complete.

## Logistic Selection

For inner-CV configurations:

1. Generate inner OOF predictions.
2. Calibrate on disjoint chronological data.
3. Apply pre-registered thresholds.
4. Calculate Brier and trading utility.

Selection:

1. best mean Brier;
2. retain configurations within one standard error;
3. among those, maximize expectancy per raw signal at retention >= 40 percent;
4. require positive aggregate OOF expectancy;
5. tie-break to lower C, then simpler/symmetric model.

## Direction-Interaction Scope

Admission of M1_LOGISTIC_L2_DIRINT is a model-selection step performed on inner-OOF data only.

The +0.01R inner-OOF gain criterion governs only whether the interaction model is preferred over the symmetric model during selection.

It does not lower, waive, or substitute for any final candidate gate.

Whichever model is selected, M1_LOGISTIC_L2_SYMMETRIC or M1_LOGISTIC_L2_DIRINT, must clear all absolute and incremental candidate gates on P95-stress labels.

## Calibration

Default calibration is sigmoid.

Use isotonic only when:

- calibration rows >= 2000;
- positive >= 400;
- negative >= 400.

Report:

- Brier;
- Brier skill;
- log loss;
- reliability curve;
- calibration slope and intercept;
- expected calibration error.

Uncalibrated tree probabilities cannot control the operating threshold.

## Threshold Selection

Candidate thresholds:

- 0.45;
- 0.50;
- 0.55;
- 0.60.

Also report:

- top 80 percent;
- top 60 percent;
- top 40 percent.

Eligibility:

- signal retention >= 40 percent;
- virtual-trade retention >= 35 percent;
- calibration expectancy per raw signal > 0;
- calibration PF >= 1.10.

Select maximum expectancy per raw signal.

Tie-break:

- lower threshold;
- higher retention.

Freeze before test.

ABSTAIN on:

- critical missing data;
- schema mismatch;
- model hash mismatch;
- drift lock;
- unsupported state.

## Final Historical OOS Gates

Use P95-stress labels.

Absolute gates:

- point PF >= 1.30 and PF fifth percentile > 1.00;
- point expectancy per retained trade >= +0.15R and expectancy fifth percentile > 0R;
- point expectancy per raw signal > 0R and raw-signal expectancy fifth percentile > 0R.

Incremental gates versus the selected deterministic rule:

- point delta_R per raw signal > 0;
- delta_R fifth percentile > 0;
- and either point expectancy improvement >= +0.03R or point PF improvement >= +0.10.

Other gates:

- signal retention >= 40 percent;
- trade retention >= 35 percent;
- P95 cost_R <= 0.15;
- no accepted trade cost_R > 0.15;
- max consecutive losses <= 8;
- max drawdown <= 8R;
- largest trade contribution <= 10 percent net PnL;
- top five contribution <= 40 percent;
- single positive day contribution <= 30 percent;
- at least 3 of 4 primary weekly buckets PF >= 1;
- both directions represented;
- all required regimes represented.

If point estimates pass but lower bounds do not, status is CONTINUE_EVIDENCE.

If the selected model fails any final gate, resolve as CONTINUE_EVIDENCE or NO-GO under this protocol.

Do not weaken gates.
