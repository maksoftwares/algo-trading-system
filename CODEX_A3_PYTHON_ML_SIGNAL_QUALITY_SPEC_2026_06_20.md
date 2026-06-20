# CODEX SPEC — Python ML Signal-Quality Layer for XAUUSD A3

**Project:** `maksoftwares/algo-trading-system`  
**Account scope:** A3 / `1033669`  
**Symbol:** `XAUUSD` only  
**Base family:** `breakout_retest` only  
**Mode:** Python research + shadow scoring only  
**Broker action:** prohibited  
**Existing A3 lanes:** `933200`, `933300`, `933400` remain paused  
**Profit-lock manager:** remains dry-run/disarmed  
**Canonical Phase 2 / live / real capital:** unchanged and blocked  

---

# 0. Instruction to Codex

Implement this specification one task per commit.

Do not:

- modify or reactivate `933200`, `933300`, or `933400`;
- attach an armed EA;
- send, modify, or close broker orders;
- enable a preset;
- use Python `MetaTrader5.order_send`;
- add a Python service to the broker execution path;
- edit existing SHA256-locked hypothesis files;
- train on the final forward holdout;
- use random train/test shuffling;
- deploy a model merely because classification accuracy looks good;
- use reinforcement learning, neural networks, LLMs, AutoML, Optuna, or a large hyperparameter search in V1.

The objective is to determine whether Python can rank existing, deterministic breakout-retest signals by future quality while retaining useful trade frequency.

---

# 1. Executive decision

Yes, Python machine learning is a valid possibility.

The safest first use is not to let Python invent trades. It should act as a **meta-labeling signal-quality layer**:

```text
Deterministic breakout-retest engine generates a raw would-signal
                         ↓
Python receives only information available at decision time
                         ↓
Model estimates signal quality
                         ↓
Shadow output:
  TAKE
  SKIP
  ABSTAIN
  calibrated probability
  expected net-R bucket
  explanation fields
                         ↓
No broker action
```

The model must leave these unchanged:

```text
direction
entry construction
stop construction
1.50R target
lot
risk
account
magic number
position management
```

The model answers only:

```text
“Given that the existing engine produced this signal,
is this signal more likely than usual to survive costs
and reach a profitable outcome?”
```

This is materially safer and easier to validate than a model that generates direction, price, stop, target, or size.

---

# 2. What the current three weeks can and cannot do

## 2.1 What can be done now

The existing observations can be used immediately to:

- build and validate the data pipeline;
- deduplicate signals;
- define features;
- define labels;
- audit leakage;
- reproduce historical signals;
- train an exploratory regularized model;
- measure feature importance;
- compare simple rules with machine learning;
- run shadow scoring;
- discover data-quality problems;
- start a newly locked forward window.

## 2.2 What cannot be claimed

Three weeks should not be treated as production-grade evidence by itself.

Calendar duration is not the only issue. The model needs:

- enough unique base signals;
- enough winners and losers;
- long and short examples;
- rising, falling, and mixed XAU regimes;
- multiple volatility conditions;
- multiple sessions;
- enough independent days;
- a genuinely untouched future window.

The recent three weeks have already influenced reviews and feature ideas. They are therefore:

```text
DISCOVERY / DEVELOPMENT DATA
```

They are not a clean final holdout.

The final forward holdout must begin only after:

- the feature registry is locked;
- the label contract is locked;
- the model set is locked;
- model-selection rules are locked;
- the score threshold is locked;
- the source commit and artifact hashes are recorded.

---

# 3. Use all would-signals, not only executed trades

Training on executed A3 trades alone would create severe selection bias.

Create one row for every unique raw breakout-retest signal, including:

- executed historical signals;
- duplicate signals;
- rejected signals;
- session-blocked signals;
- cost-blocked signals;
- trend-blocked signals;
- all future shadow signals.

Give every signal a counterfactual tick-level virtual outcome under the same fixed entry/SL/TP contract.

This allows the model to learn from:

```text
what was traded
what was not traded
what would have won
what would have lost
what failed because of entry quality
what went green and then gave back
```

Duplicates from different EAs must not be independent training rows.

---

# 4. Recommended ML use cases

## 4.1 V1 — entry-quality meta-labeler

Primary task:

```text
Predict whether a raw breakout-retest signal should be taken.
```

Model inputs are available before virtual entry.

Primary output:

```text
p_win_calibrated
```

Secondary output:

```text
quality_score
```

Primary label:

```text
y_win = 1 when the fixed virtual trade finishes with net_R > 0
y_win = 0 when the fixed virtual trade finishes with net_R <= 0
```

Also store:

```text
y_net_R
```

but do not make regression the primary V1 model.

## 4.2 V2 — exit-giveback research

Later and separately:

```text
Predict whether an already-open virtual trade that reached +0.50R
is likely to give back the profit before TP.
```

Do not combine the entry model and exit model in the same initial experiment.

## 4.3 Drift/anomaly monitor

Later and separately:

```text
Detect when live feature distributions,
model probabilities, or realized outcomes drift
away from the training distribution.
```

## 4.4 Prohibited V1 use cases

Do not use ML to:

- choose BUY versus SELL;
- create new entries;
- select stop distances;
- select TP;
- change risk;
- change lots;
- average down;
- manage recovery;
- decide when to rearm A3;
- learn online after every trade;
- overwrite model weights automatically;
- interpret news through an LLM;
- use an LLM in the order path.

---

# 5. Required Python environment

Create a dedicated locked environment.

Suggested packages:

```text
numpy
pandas
pyarrow
scipy
scikit-learn
joblib
pydantic
pyyaml
matplotlib
MetaTrader5
```

Later export-only packages:

```text
onnx
onnxruntime
skl2onnx
```

Optional only after V1 proves dataset adequacy:

```text
xgboost
shap
```

Do not add in V1:

```text
tensorflow
torch
keras
river
optuna
autogluon
h2o
auto-sklearn
```

Create:

```text
requirements-ml-a3.in
requirements-ml-a3-lock.txt
ML_ENVIRONMENT_MANIFEST.json
```

The manifest must record:

```text
Python version
OS
package versions
git commit
timezone package version
MetaTrader5 package version
CPU architecture
random seeds
```

---

# 6. Required repository layout

Add under:

```text
xau-usd/xauusd-phase1/
```

Structure:

```text
ml/a3_meta_v1/
  __init__.py
  schema.py
  signal_id.py
  data_sources.py
  data_audit.py
  labels.py
  features.py
  feature_registry.py
  splits.py
  purging.py
  models.py
  calibration.py
  thresholding.py
  metrics.py
  trading_metrics.py
  explanations.py
  registry.py
  export.py
  drift.py

config/ml/
  a3_meta_v1.yaml

docs/
  A3_ML_META_LABEL_HYPOTHESIS_V1.md
  A3_ML_DATA_CONTRACT_V1.md
  A3_ML_FEATURE_REGISTRY_V1.csv
  A3_ML_LABEL_CONTRACT_V1.md
  A3_ML_VALIDATION_PROTOCOL_V1.md
  A3_ML_MODEL_SELECTION_PROTOCOL_V1.md
  A3_ML_SHADOW_GOVERNANCE_V1.md
  A3_ML_RETRAINING_POLICY_V1.md

outputs/manifests/
  A3_ML_V1_LOCK_MANIFEST.json

scripts/
  build_a3_ml_dataset.py
  audit_a3_ml_dataset.py
  train_a3_ml_baselines.py
  evaluate_a3_ml_walkforward.py
  calibrate_a3_ml_model.py
  select_a3_ml_threshold.py
  score_a3_ml_shadow.py
  export_a3_ml_model.py
  verify_a3_ml_artifacts.py
  generate_a3_ml_model_report.py
  generate_a3_ml_drift_report.py

tests/
  test_a3_ml_signal_id.py
  test_a3_ml_data_contract.py
  test_a3_ml_no_leakage.py
  test_a3_ml_labels.py
  test_a3_ml_features.py
  test_a3_ml_splits.py
  test_a3_ml_purging.py
  test_a3_ml_models.py
  test_a3_ml_calibration.py
  test_a3_ml_thresholding.py
  test_a3_ml_metrics.py
  test_a3_ml_artifact_hashes.py
  test_a3_ml_shadow_safety.py

outputs/ml/a3_meta_v1/
  data/
  models/
  reports/
  manifests/
  shadow/
```

Do not place raw tick history in Git.

Commit only manifests, summaries, schemas, and small reproducible fixtures.

---

# 7. Data sources

The dataset builder may read:

```text
raw breakout-retest observer decisions
planned A3 signal-quality observer decisions
M5 / M15 / H1 / H4 / D1 bars
tick data
measured spread logs
actual broker history
virtual trade events
position-path logs
session and time metadata
```

Use actual broker history only to validate executed-trade reconstruction.

Use tick-level virtual execution to label every unique raw signal.

Never use:

```text
future bars
final trade PnL as an input feature
MFE/MAE as an entry feature
exit reason as an entry feature
future spread
future session outcome
account balance after the signal
daily PnL after the signal
model scores generated after the signal
manual reviewer labels as market-outcome labels
```

---

# 8. Signal identity and deduplication

Create a deterministic `signal_id`.

Required components:

```text
account_scope
symbol
base_family
direction
level_kind
normalized_level_price
break_bar_time_utc
retest_bar_time_utc
confirmation_bar_time_utc
```

Example conceptual value:

```text
A3|XAUUSD|BREAKOUT_RETEST|BUY|SWING_HIGH|4342.500|
20260618T120000|20260618T123000|20260618T123500
```

Hash to a stable SHA256 or compact deterministic ID.

Rules:

- Same market setup emitted by `933200`, `933300`, or `933400` maps to one base `signal_id`.
- Keep lane-level rows as attribution records.
- Build the training dataset from one row per unique `signal_id`.
- Store duplicate count and lane list as metadata.
- Duplicate count must not be used as an entry feature.
- Train/test splitting must keep the whole signal group in one split.

---

# 9. Feature-time contract

Each row has:

```text
feature_time_utc
decision_time_utc
entry_eligible_from_utc
label_end_time_utc
```

Hard requirements:

```text
feature_time_utc <= decision_time_utc
decision_time_utc < entry_eligible_from_utc
all input bars are completed before decision_time_utc
label data starts after decision_time_utc
```

Any violation:

```text
DATA_LEAKAGE_FAIL
```

The pipeline must stop.

---

# 10. Exact V1 feature registry

Cap V1 at no more than 35 model features.

Use values available at signal decision time.

## 10.1 Signal geometry

```text
direction_code
level_kind
break_distance_atr
break_body_atr
break_body_ratio
break_close_location
bars_break_to_retest
retest_penetration_atr
retest_close_distance_atr
retest_range_atr
bars_retest_to_confirmation
confirmation_body_atr
confirmation_body_ratio
confirmation_close_location
confirmation_opposite_wick_ratio
first_retest_flag
```

## 10.2 Trend and impulse

```text
m15_ema20_slope_atr
h1_ema20_slope_atr
h4_ema20_slope_atr
d1_ema20_minus_ema50_atr
price_minus_m15_ema20_atr
price_minus_h1_ema20_atr
ret_3_m5_atr
ret_12_m5_atr
ret_48_m5_atr
impulse_alignment_12
```

All slopes and returns must be normalized by an appropriate ATR or risk scale where possible.

## 10.3 Volatility and cost

```text
m5_atr_points
m5_atr_percentile_20d
h1_atr_percentile_60d
spread_points
spread_percentile_session_20d
stop_distance_points
cost_R
tick_volume_ratio_20
range_compression_ratio_20
```

## 10.4 Time and session

```text
dubai_hour_sin
dubai_hour_cos
day_of_week
session_bucket
minutes_from_session_start
```

## 10.5 Context flags

```text
d1_bias
h1_trend_alignment
m15_trend_alignment
data_complete_flag
```

Do not add additional indicators during V1 without creating a new versioned registry and lock.

---

# 11. Missing-data policy

Do not silently impute unavailable market context with zero.

Rules:

```text
Missing critical signal geometry:
  reject row from model scoring
  log DATA_INCOMPLETE_SIGNAL

Missing MTF feature:
  retain row only if the pre-registered model allows missingness
  set explicit missing flag

Missing tick label:
  label_status = UNRESOLVED
  exclude from supervised training
  include in data audit

Missing spread:
  label_status = UNRESOLVED_COST
  do not replace with median silently
```

For logistic regression:

```text
critical feature missing = row excluded
noncritical feature missing = training-only median imputation
missing-indicator flag added
```

The imputer must be fitted only on the training fold.

---

# 12. Labels

Labels must come from the deterministic tick-level virtual execution engine.

Use the same:

```text
entry timing
bid/ask side
stop floor
spread handling
1.50R TP
1.00R initial risk
holding horizon
gap logic
timeout logic
```

as the locked implementation contract.

If the contract does not define holding horizon and timeout behavior, stop and create a hash-locked addendum before dataset construction.

Required labels:

```text
y_win
y_net_R
y_outcome
y_loss_class
y_MFE_R
y_MAE_R
y_holding_seconds
```

Allowed `y_outcome`:

```text
TP
SL
TIMEOUT_POSITIVE
TIMEOUT_NEGATIVE
TIMEOUT_FLAT
DATA_UNRESOLVED
```

Primary V1 binary label:

```text
y_win = 1 when y_net_R > 0
y_win = 0 when y_net_R <= 0
```

Rows with `DATA_UNRESOLVED` are not trainable.

Also report results with pure `TP` versus `SL` labels as a sensitivity analysis.

---

# 13. Entry-versus-exit loss classes

Use path order.

```text
BAD_SIGNAL:
  -0.50R reached before +0.50R
  OR +0.50R was never reached before the final loss

MIXED:
  +0.50R reached first
  but MFE stayed below +0.75R
  and the trade later lost

BAD_EXIT_GIVEBACK:
  +0.75R reached before -0.50R
  and final result <= 0R

NEAR_TP_GIVEBACK:
  +1.25R reached
  +1.50R TP not reached
  final result <= 0R
```

The entry model should primarily reduce `BAD_SIGNAL`.

Do not judge the entry model only by total losses if give-back losses remain unchanged.

---

# 14. Dataset eligibility gates

Generate `A3_ML_DATA_AUDIT.md`.

Statuses:

## 14.1 `PIPELINE_ONLY`

Use when any applies:

```text
< 300 unique labeled signals
< 75 positive labels
< 75 negative labels
< 8 active market weeks
only one direction represented
only one major market regime represented
```

Permitted:

```text
pipeline tests
feature audit
descriptive analysis
no model-selection claim
```

## 14.2 `EXPLORATORY_MODEL`

Minimum:

```text
>= 300 unique labeled signals
>= 75 wins
>= 75 losses
>= 8 active weeks
both directions
at least two regimes
```

Permitted:

```text
regularized logistic regression
shadow research
no model promotion
```

## 14.3 `CANDIDATE_MODEL`

Minimum:

```text
>= 1000 unique labeled signals
>= 200 wins
>= 200 losses
>= 16 active market weeks
both directions
rising, falling, and mixed/sideways regimes
session coverage
P95 cost coverage
```

Permitted:

```text
logistic versus shallow gradient boosting comparison
locked forward shadow candidate
```

The recent three weeks may contribute to discovery, but final candidate evaluation needs new post-lock evidence.

---

# 15. Data splitting and leakage prevention

Never use:

```text
train_test_split(shuffle=True)
KFold(shuffle=True)
StratifiedKFold with random ordering
random row sampling
```

Implement custom purged expanding walk-forward validation.

Each sample has:

```text
event_start = decision_time_utc
event_end = label_end_time_utc
```

For each fold:

1. training occurs strictly before the validation/test block;
2. remove every training sample whose event interval overlaps the test interval;
3. apply an embargo after the test block;
4. keep every duplicate signal group together;
5. fit preprocessors only on training data;
6. calibrate only on a later disjoint calibration block;
7. choose threshold only on calibration data;
8. evaluate once on the untouched outer test block.

Minimum structure:

```text
5 outer expanding walk-forward folds
3 inner expanding folds for the small pre-registered model grid
purge = full label overlap
embargo = max(label horizon, one M5 bar)
```

The current three-week reviewed window must not be reused as a final unbiased test if it informed feature design.

---

# 16. Model families

Pre-register exactly these models.

## 16.1 `M0_BASE_RATE`

```text
constant probability = training-fold win rate
```

Purpose:

```text
calibration baseline
Brier-skill baseline
```

## 16.2 `M1_LOGISTIC`

Regularized logistic regression.

Pipeline:

```text
numeric:
  training-fold median imputer where allowed
  StandardScaler

categorical:
  OneHotEncoder(handle_unknown="ignore")

estimator:
  LogisticRegression
```

Pre-registered `C` grid:

```text
0.1
1.0
10.0
```

Selection metric:

```text
validation Brier score
```

Tie-break:

```text
stronger regularization
fewer effective coefficients
```

This is the primary V1 model.

## 16.3 `M2_HIST_GB`

Only run when dataset status is `CANDIDATE_MODEL`.

Use shallow histogram gradient boosting.

Pre-registered configurations:

```text
A:
  max_depth=2
  max_leaf_nodes=7
  min_samples_leaf=50
  learning_rate=0.03
  max_iter=200
  l2_regularization=1.0

B:
  max_depth=3
  max_leaf_nodes=15
  min_samples_leaf=75
  learning_rate=0.03
  max_iter=200
  l2_regularization=2.0
```

Set:

```text
early_stopping=False
```

Use the project’s own chronological validation rather than the estimator’s internal random validation behavior.

Recommended monotonic constraints where defensible:

```text
cost_R: non-increasing approval probability
spread_points: non-increasing
retest_penetration_atr: non-increasing
```

Do not force monotonicity on uncertain features.

## 16.4 Model selection rule

The more complex model can replace logistic only when, in outer OOS results:

```text
mean expectancy improvement >= +0.03R
OR mean PF improvement >= +0.10

AND signal retention is not lower by more than 10 percentage points

AND Brier skill is not worse

AND no extra fold becomes unprofitable

AND feature importance is stable
```

Otherwise select logistic.

If neither model beats the deterministic frequency-preserving filters, do not use ML.

---

# 17. Probability calibration

Calibrate only after the base model is selected within each training fold.

Use disjoint chronological calibration data.

Default:

```text
sigmoid calibration
```

Use isotonic only when:

```text
calibration rows >= 1000
and each class has >= 200 rows
```

Report:

```text
Brier score
log loss
reliability curve
calibration intercept
calibration slope
expected calibration error
```

Do not use uncalibrated tree probabilities for live threshold decisions.

---

# 18. Threshold selection

Pre-register candidate thresholds:

```text
0.45
0.50
0.55
0.60
```

Also report score-retention bands:

```text
top 80%
top 60%
top 40%
```

Threshold selection uses calibration data only.

Lexicographic selection:

```text
1. signal retention >= 40%
2. virtual-trade retention >= 35%
3. calibration PF >= 1.20
4. calibration expectancy > 0R
5. maximize calibration expectancy
6. if tied, choose the lower threshold to preserve frequency
```

Freeze the selected threshold before final OOS scoring.

The test block may not alter it.

Add an abstention rule:

```text
ABSTAIN when critical data is missing
ABSTAIN when model artifact/schema hash does not match
ABSTAIN when drift lock is active
```

Do not use a wide probability uncertainty band in V1 unless pre-registered, because it can silently collapse frequency.

---

# 19. Metrics

## 19.1 ML metrics

Report:

```text
Brier score
Brier skill versus base-rate model
log loss
ROC-AUC
PR-AUC
calibration slope/intercept
expected calibration error
```

Accuracy is informational only.

## 19.2 Trading metrics

Report at every threshold:

```text
raw signals
retained signals
signal retention %
opened virtual trades
trade retention %
wins
losses
win rate
PF
net expectancy R
net R
max drawdown R
max consecutive losses
P50 cost_R
P95 cost_R
largest trade contribution
top-five contribution
best-day contribution
weekly PF
long/short metrics
session metrics
regime metrics
BAD_SIGNAL share
give-back share
```

## 19.3 Score quality

Create probability deciles.

Required pattern:

```text
higher score deciles should have higher win rate
higher score deciles should have higher net expectancy
```

Report:

```text
Spearman rank correlation:
  score versus outcome
  score versus net_R
```

A model whose top score bucket is not better than its middle/bottom buckets fails.

## 19.4 Confidence intervals

Use block bootstrap by day or week, not individual rows.

Report 95% confidence intervals for:

```text
PF
expectancy
win rate
retention
drawdown
```

---

# 20. Comparison baselines

Every report must include:

```text
B0 raw breakout-retest
F_LOOSE_CT_VETO
F_H1_ALIGN
F_RETEST_LIGHT
best locked deterministic candidate
M1 logistic
M2 shallow HistGradientBoosting, when eligible
```

ML must provide material value beyond a simple rule.

Minimum incremental-value gate versus best deterministic rule at comparable retention:

```text
expectancy improvement >= +0.03R
OR PF improvement >= +0.10
```

If not:

```text
select the simpler deterministic rule
retire the ML candidate
```

---

# 21. Model pass gates

A model is eligible for a newly locked forward shadow candidate only when all apply:

```text
dataset status = CANDIDATE_MODEL
all leakage tests PASS
all outer folds completed
Brier skill > 0 on average
no catastrophic Brier degradation in any fold
score-decile relationship directionally monotonic
signal retention >= 40%
virtual-trade retention >= 35%
PF >= 1.30 after executable costs
net expectancy >= +0.15R
P95 cost_R <= 0.15R
no accepted trade cost_R > 0.15R
max consecutive losses <= 8
max drawdown <= 8R
largest trade contribution <= 10%
top five contribution <= 40%
single-day positive contribution <= 30%
at least 3 of 4 weekly buckets PF >= 1
both directions represented
rising and falling regimes represented
model beats deterministic benchmark materially
```

Win-rate rule:

```text
For the currently locked V1:
  retain the locked >=50% gate.

For a future ML-specific V1:
  pre-register one of:
    hard floor >=45%, target >=50%
  OR
    hard >=50%

Do not choose after viewing results.
```

---

# 22. Holdout and forward evidence

## 22.1 Historical discovery

Use older historical data and the reviewed three-week window for:

```text
feature engineering
data debugging
model discovery
benchmark comparison
```

## 22.2 Locked final forward window

After model and threshold lock, start a new forward window.

Minimum:

```text
>= 100 closed model-retained virtual trades
>= 20 active market days
>= 4 calendar weeks
>= 25 long and >= 25 short
>= 3 weeks with >= 15 retained trades
rising and falling XAU regime
```

The final forward window is never used for:

```text
feature selection
model selection
hyperparameter selection
calibration
threshold selection
```

---

# 23. Feature explanations

For logistic regression, report:

```text
standardized coefficient
sign
absolute magnitude
fold stability
local contribution per scored signal
```

For tree model, report:

```text
permutation importance on OOS data
importance mean and standard deviation
importance stability across folds
```

Do not rely only on built-in impurity importance.

Generate for each shadow score:

```text
top_positive_reason_1
top_positive_reason_2
top_negative_reason_1
top_negative_reason_2
```

These are explanations, not execution rules.

---

# 24. Shadow integration architecture

## 24.1 Phase A — offline

Python reads frozen logs and produces scores.

No MT5 changes.

Outputs:

```text
a3_ml_offline_scores.csv
A3_ML_OFFLINE_REPORT.md
```

## 24.2 Phase B — live shadow Python scorer

Python tails a passive feature log and writes:

```text
a3_ml_shadow_scores.csv
```

Fields:

```text
timestamp_utc
signal_id
model_id
model_hash
feature_schema_hash
p_win_raw
p_win_calibrated
selected_threshold
ml_action_shadow
score_decile
drift_status
top_reason_1
top_reason_2
```

The Python process must not import or call:

```text
MetaTrader5.order_send
order_check
position modification
broker execution functions
```

It may use the MetaTrader5 package only for read-only bars/ticks/account verification.

## 24.3 Phase C — MQL5 observer parity

Later create:

```text
mt5/Experts/Account3MLShadowObserver.mq5
mt5/Include/A3MLFeatureVector.mqh
```

It logs features and optionally runs an embedded model in passive mode.

No broker action.

## 24.4 Phase D — export

Preferred for logistic:

```text
export coefficients, intercept, feature order,
category mapping, scaler means/scales, and threshold
to a signed JSON artifact
```

Implement exact scoring in MQL5 and require probability parity.

For a tree model:

```text
export ONNX
verify ONNX Runtime versus Python
verify MQL5 ONNX versus Python
```

Required parity:

```text
same features
same probability within 1e-6 for logistic
same action on 100% of acceptance-boundary fixtures
>=99.9% probability/action parity across replay sample
```

Do not place a Python network/RPC dependency in the future broker execution path.

---

# 25. Model registry

Every model version requires:

```text
model_id
model_family
model_version
source_commit
training_code_hash
training_data_manifest_hash
feature_registry_hash
label_contract_hash
split_manifest_hash
hyperparameters
random_seed
calibration_method
selected_threshold
training window
calibration window
test windows
forward_start_utc
model artifact hash
ONNX/JSON artifact hash
metrics
limitations
approval state
```

Create:

```text
A3_ML_MODEL_CARD_<model_id>.md
A3_ML_MODEL_MANIFEST_<model_id>.json
```

No model is addressed by a mutable filename such as:

```text
model_latest.pkl
```

---

# 26. Retraining policy

No online self-learning.

A model cannot update itself after each trade.

Retraining eligibility:

```text
at least 250 new resolved unique signals
AND at least 4 new active market weeks
```

Every retrain:

```text
new model version
new artifact hash
same locked feature/label contract or new version
full walk-forward validation
new forward shadow window
reviewer signoff
```

The currently approved model remains frozen until the replacement passes.

No automatic model promotion.

---

# 27. Drift controls

Track:

```text
feature missing rate
feature distribution drift
score distribution drift
win-rate/base-rate drift
Brier drift
calibration drift
retention drift
PF/expectancy drift
session mix
direction mix
regime mix
```

Suggested shadow alerts:

```text
critical feature missing > 1%
score PSI > 0.25
retention changes by > 20 percentage points
Brier score worsens > 25% versus locked OOS
100-signal rolling expectancy <= 0R
100-signal rolling PF < 1.0
unseen category or schema mismatch
```

Drift response:

```text
ML_SHADOW_DISABLED
```

A future execution model must fail open to the deterministic paused/no-trade policy, not force an ML trade.

---

# 28. Required tests

## Data

```text
duplicate signal collapse
stable signal_id
timezone normalization
completed-bar-only feature use
feature timestamp <= decision timestamp
label starts after decision
no train/test group overlap
no label-horizon overlap after purging
embargo applied
all preprocessors training-fold-only
```

## Labels

```text
long bid/ask correctness
short bid/ask correctness
TP-before-SL
SL-before-TP
gap exit
timeout
missing tick
restart recovery
spread not double-counted
```

## Models

```text
deterministic random seeds
model grid exactly pre-registered
logistic coefficient reproducibility
tree depth/leaf constraints
calibration uses disjoint data
isotonic sample gate
threshold cannot read test metrics
```

## Safety

```text
no order_send import/call
no broker write API
no armed preset
no existing A3 EA modification
A3 pause state unchanged
all outputs marked shadow-only
```

## Artifact integrity

```text
feature registry hash matches
label contract hash matches
dataset manifest hash matches
model artifact hash matches
threshold manifest matches
environment manifest matches
```

---

# 29. Required reports

```text
A3_ML_DATA_AUDIT.md
A3_ML_DATA_MANIFEST.json
A3_ML_FEATURE_AUDIT.md
A3_ML_LABEL_AUDIT.md
A3_ML_LEAKAGE_AUDIT.md
A3_ML_SPLIT_MANIFEST.json
A3_ML_WALK_FORWARD_REPORT.md
A3_ML_CALIBRATION_REPORT.md
A3_ML_THRESHOLD_REPORT.md
A3_ML_TRADING_METRICS_REPORT.md
A3_ML_SCORE_DECILE_REPORT.md
A3_ML_FEATURE_IMPORTANCE_REPORT.md
A3_ML_DETERMINISTIC_BENCHMARK_REPORT.md
A3_ML_MODEL_CARD.md
A3_ML_ARTIFACT_VERIFICATION_REPORT.md
A3_ML_SHADOW_FORWARD_REPORT.md
A3_ML_DRIFT_REPORT.md
A3_ML_FINAL_VERDICT.md
```

---

# 30. One task per commit

## `ML-00` — data inventory

```text
Audit all existing signal, trade, tick, spread, bar,
and position-path artifacts.

Produce row counts, dates, uniqueness, class balance,
directions, sessions, regimes, missingness, and duplicate rate.

No training.
```

## `ML-01` — lock contracts

```text
Add:
  hypothesis
  data contract
  feature registry
  label contract
  validation protocol
  model-selection protocol

Compute SHA256 manifest.

No training.
```

## `ML-02` — dataset builder

```text
Build one row per unique raw signal.
Join decision-time features.
Join tick-level virtual labels.
Add audit checks.

No model.
```

## `ML-03` — leakage-safe splitter

```text
Implement purged expanding walk-forward splits.
Add overlap and embargo tests.
Generate split manifest.

No model.
```

## `ML-04` — logistic baseline

```text
Add M0 and M1.
Generate OOS scores only.
No tree model.
No threshold deployment.
```

## `ML-05` — calibration and thresholding

```text
Add sigmoid calibration.
Apply pre-registered threshold selection.
Generate calibration and retention reports.
```

## `ML-06` — deterministic comparison

```text
Compare model against:
  raw baseline
  loose counter-trend veto
  H1 alignment
  light retest

No model promotion.
```

## `ML-07` — shallow tree research

Only when dataset status is `CANDIDATE_MODEL`.

```text
Add M2 with exactly two pre-registered configurations.
Compare against M1.
```

## `ML-08` — explanations and model registry

```text
Add coefficient/permutation reports.
Write model card and manifest.
Hash artifacts.
```

## `ML-09` — offline shadow scoring

```text
Score frozen historical and discovery data.
No live tailing.
```

## `ML-10` — live shadow scorer

After safety review:

```text
Read passive feature log.
Write shadow score log.
No broker actions.
```

## `ML-11` — MQL feature parity

```text
Build passive MQL feature logger.
Compare Python and MQL feature vectors.
No model execution.
```

## `ML-12` — export parity

```text
Export logistic JSON or tree ONNX.
Verify Python/ONNX/MQL parity.
No order actions.
```

## `ML-13` — locked forward shadow

```text
Record new forward_start_utc.
Freeze model, threshold, and artifacts.
Collect full minimum sample.
```

## `ML-14` — verdict

```text
PASS
FAIL
or CONTINUE_SHADOW

No automatic reactivation.
```

---

# 31. NO-GO conditions

The ML layer remains research-only if any applies:

```text
fewer than 1000 unique candidate-model signals
recent reviewed data used as final holdout
unresolved signal duplicates
feature leakage
random split used
purge/embargo missing
feature or label contract hash mismatch
model grid changed after results
threshold selected from test data
calibration data overlaps training
unresolved Python/MQL feature mismatch
model does not beat deterministic rules
retention below 40%
trade retention below 35%
PF below 1.30
expectancy below +0.15R
P95 cost_R above 0.15R
score deciles are not ordered
probabilities are materially uncalibrated
one regime carries the model
concentration gate fails
drift lock active
existing A3 lane modified
A3 broker action proposed
model automatically retrains
Python broker execution API present
CI is not green
independent review absent
```

---

# 32. Minimum evidence before discussing ML-assisted demo execution

```text
1. A3 remains paused with zero exposure.
2. Data audit PASS.
3. At least 1000 unique labeled signals.
4. Feature and label contracts locked.
5. Leakage audit PASS.
6. Purged walk-forward validation complete.
7. Logistic baseline complete.
8. Complex model, if used, materially beats logistic.
9. Model materially beats deterministic rule benchmark.
10. Probability calibration PASS.
11. Frequency floor PASS.
12. PF/expectancy/cost/drawdown/concentration gates PASS.
13. Python/MQL feature parity PASS.
14. Export parity PASS.
15. New untouched forward shadow minimum completed.
16. Drift controls implemented.
17. Model card and artifact hashes committed.
18. Account-wide family mutex built and tested.
19. Containment built and tested.
20. Independent reviewer signoff.
21. Owner authorization of exact model/source/binary hashes.
22. One-lane, 0.01-lot, time-limited micro-pilot plan.
```

---

# 33. Explicitly out of scope

```text
No autonomous AI trader
No reinforcement learning
No deep learning
No LSTM/transformer
No LLM execution decisions
No direct Python order placement
No automatic online retraining
No model-selected lot size
No model-selected SL/TP
No round-family promotion
No combining A3 lanes
No reactivation of 933200/933300/933400
No live or real capital
No changing existing locked hypotheses
```

---

# 34. Codex’s first instruction

```text
Do not train a model first.

First:
  inventory and audit the data;
  count unique resolved base signals;
  prove that all features are available at decision time;
  prove that counterfactual labels can be generated for all signals;
  declare PIPELINE_ONLY / EXPLORATORY_MODEL / CANDIDATE_MODEL.

Then:
  lock the data, feature, label, split, model, and threshold protocols.

Only after that:
  implement regularized logistic regression.
```

---

# 35. Bottom line

The recommended system is:

```text
Existing deterministic breakout-retest signal
+
Python meta-label quality probability
+
strict leakage-safe validation
+
frequency floor
+
shadow-only forward proof
```

Python can make the system smarter, but only if it is used as a measurable statistical layer.

The first success criterion is not:

```text
“AI makes money.”
```

It is:

```text
“On signals the EA already knows how to generate,
a simple, calibrated, reproducible Python model identifies
a higher-quality subset that beats both the raw EA
and simple deterministic filters without killing frequency.”
```

If the model cannot do that, retire the ML layer and keep the simpler deterministic solution.
