# EURUSD Neutral walk-forward preregistration

Status: `LOCKED_BEFORE_WALKFORWARD_OUTCOME_INSPECTION`

## Independent hypothesis

The fixed-rule Neutral campaign failed because every hand-authored entry family won only about 28–32% of its trades. The next mechanism is not a threshold repair. It is a regularized, low-capacity classifier that estimates whether a 6-pip target will precede a 4-pip stop using a fixed set of completed-bar features.

The full-calendar oracle is excluded from features, labels, fitting, threshold selection, and trade generation. It remains an evaluation-only imitation benchmark.

## Dataset and causality

Candidates occur every 15 minutes. Each candidate uses the latest completed M5 bar and the latest cross-asset state available no later than completion-hour minus one hour. Only non-shock, non-joint-compression `NEUTRAL` states are eligible.

Each timestamp produces a long and short training row. The supervised label is one only when that side’s executable 6-pip target occurs before its 4-pip stop within 12 hours. Future paths create historical training labels only; they are never available to an inference row until its complete label lifecycle has elapsed.

## Frozen features

The model receives side-aligned, volatility-normalized:

- 1, 3, 6, 12, and 24-bar returns;
- 12/48-bar EMA separation and price/EMA-anchor distance;
- completed-bar close location and range;
- distance to the preceding twelve-bar high or low;
- completed tick-count ratio to its preceding 24-bar median;
- lagged DXY, EURUSD, and bond EMA separations;
- lagged cross-asset compression/volatility measures;
- UTC hour and weekday cyclical encodings.

All rolling extremes and tick baselines exclude the current bar. Inputs are clipped only at the frozen broad bound.

## Model and selection

The model is a single L2 logistic regression with `C=0.10`; its scaler and coefficients are fit only on eligible past rows.

It is initially fit on 2019–2020. One probability threshold is selected on 2021–2022 from the nine frozen values 0.35 through 0.55. A threshold is development-qualified only with at least 100 routed trades and PF at least 1.05 in each of 2021 and 2022. The deterministic score is the lower annual PF, then total net R.

No model parameter or threshold may be repaired from 2023 onward.

## Walk-forward evaluation

At the beginning of 2023, 2024, 2025, and 2026, the scaler and classifier are refit using all rows whose outcome lifecycle ended strictly before that window. The threshold remains fixed.

At each timestamp, only the higher-probability side can trade, provided it clears the threshold. Routing permits one open position and at most four trades per UTC date.

## Admission

Every walk-forward window must contain at least 50 trades with 45–55% wins, payoff 1.35–1.75, PF at least 1.10, and positive expectancy. Overall drawdown must not exceed 30R; top-5%-winner removal and another 0.50-pip round trip must remain positive.

All archive history was inspected in earlier campaigns. Consequently, even a pass is adaptive historical evidence requiring prospective confirmation, not proof of a non-overfit live edge.
