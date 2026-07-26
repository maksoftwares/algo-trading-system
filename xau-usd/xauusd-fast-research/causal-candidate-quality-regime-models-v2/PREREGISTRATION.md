# Causal Candidate Quality Regime Models V2

## Purpose

V1's pooled candidate-quality model failed its locked incremental-evidence
gate. V2 tests one independent probability model per canonical specialist
family. It asks whether causal information can rank candidates *inside* a
regime/family without asking one estimator to learn incompatible market
mechanisms.

This is development evidence on already exposed history. Even a pass cannot
authorize ML shadow, demo, live, sizing, routing, filtering, or MT5 changes.
Fresh prospective confirmation is mandatory.

## Frozen population

Only the 3,752-row Step 3 canonical dataset and its purged expanding split
assignments may be used. Rows must have resolved labels, be dataset-eligible,
and pass mandatory XAU feature availability. Journey rows remain a separate
diagnostic and do not enter fitting. Historical accept/reject fields are not
features or labels.

Each `family_id` is evaluated independently. A family/fold is trainable only
when it contains at least 90 fit rows, 8 outer-calibration rows, and 15 test
rows. The expected trainable folds are frozen in the JSON contract. R2 and V25
have no qualifying folds and must report `INSUFFICIENT_EVIDENCE`; they may not
borrow test outcomes or be silently pooled with another family.

## Frozen model and features

Every trainable family uses the same L2 logistic-regression pipeline, fit-only
median imputation, fit-only standard scaling, `C=0.05`, and structural sample
weights. There is no hyperparameter search, model contest, per-family feature
selection, probability calibration, or test-driven fallback.

The same 22 causal pre-trade numeric features are used for all families. They
cover planned geometry, observation horizon, UTC cycle, spread, quote
intensity, directional returns, range, efficiency, and tick imbalance. IDs,
exact timestamps, outcomes, family labels, historical decisions, COMEX, and
future information are excluded.

Thresholds are chosen separately inside each fold's outer calibration set
using the frozen V1 utility: structural-weighted mean stressed R minus one
standard error. At least half of calibration rows and at least five rows must
remain. Test outcomes cannot change a threshold.

## Evidence gates

Each family is judged independently over its pooled out-of-time predictions.
It needs at least two folds and 60 test rows, weighted AUC at least 0.52 with a
95% five-weekday block-bootstrap lower bound above 0.50, positive lower bounds
for selected EV and selected-minus-baseline EV, PF at least 1.20, at least 50%
coverage and 40 selected rows, Brier no worse than the fit-prior comparator,
and selected candidate-quality drawdown no worse than baseline. All gates are
required.

No combined shared-account P&L or drawdown claim is permitted. Passing means
development-only evidence deserving prospective observation; failing means the
family model remains offline.
