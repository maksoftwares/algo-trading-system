# Step 4 Model Fit And Locked Walk-Forward Evaluation

Step 4 tests whether causal pre-trade information can rank or veto existing
specialist candidates. It does not generate entries, alter specialists,
simulate a shared account, or authorize demo or live execution.

The primary model uses only the locked deterministic and XAU feature blocks.
The COMEX/Databento block is excluded. No new data request, paid data request,
or API access is permitted.

The six Step 2B outer folds remain authoritative. For each fold, estimators are
fit only on `FIT`, probability calibration is learned from a chronological
tail inside `FIT`, the selection threshold is chosen only on `CALIBRATION`, and
metrics are reported once on `TEST`. Hyperparameters, threshold candidates,
metrics, bootstrap rules, and acceptance gates are frozen in the Step 4 JSON
contract before any estimator is fit.

The primary target is whether stressed executable net R is positive. Structural
episode weights are used in fitting and primary metrics. Journey actions remain
a separate failure diagnostic and cannot enter or rescue the canonical fit.

Passing the evidence gate means only that a model deserves a later integration
review. It does not attach ML to MT5, enable shadow mode, or change runtime.
