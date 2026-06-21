# A3 ML Commit 1 Contract Merge Report

Status: CONTRACTS_CREATED_TARGETED_TESTS_PASS

Scope: C00 final contract merge only.

## Boundary

- No model training.
- No threshold selection.
- No data mining.
- No MT5 runtime modification.
- No broker action.
- A3 lanes 933200, 933300, and 933400 remain paused by contract.

## Runtime Check

Profile-based runtime authorization reconciliation was run read-only and returned PASS_CURRENT_PRIOR_DRIFT_REMEDIATED.

Committed evidence paths:

```text
xau-usd/xauusd-phase1/outputs/reports/A3_ML_PREIMPLEMENT_RUNTIME_AUTH_CHECK.json
xau-usd/xauusd-phase1/outputs/reports/A3_ML_PREIMPLEMENT_RUNTIME_AUTH_CHECK.md
```

Evidence summary:

```text
boundary.read_only = true
boundary.orders_sent = false
boundary.positions_closed = false
boundary.profiles_modified = false
current_bad_rows = 0
A3 chart rows = 5 paused charts
decision = CURRENT_RUNTIME_SAFE; PRIOR_A3_DRIFT_REMEDIATED; KEEP_RECONCILIATION_STANDING
```

The read-only MetaTrader5 API position/order query could not be completed in this environment because the available Python runtime does not have the MetaTrader5 package installed. Therefore current open-position/order verification is not claimed complete in this report. C01 pre-lock verification must complete that query or fail closed.

## Changed File Manifest

Added the 16 final owning contract files:

- docs/A3_ML_META_LABEL_HYPOTHESIS_V1.md
- docs/A3_ML_DATA_CONTRACT_V1.md
- docs/A3_ML_SIGNAL_GROUPING_CONTRACT_V1.md
- docs/A3_ML_EXECUTION_LABEL_CONTRACT_V1.md
- docs/A3_ML_SLIPPAGE_MODEL_CONTRACT_V1.md
- docs/A3_ML_FEATURE_REGISTRY_V1.csv
- docs/A3_ML_FEATURE_BUDGET_CONTRACT_V1.md
- docs/A3_ML_REGIME_CONTRACT_V1.md
- docs/A3_ML_DIRECTION_ASYMMETRY_PROTOCOL_V1.md
- docs/A3_ML_VALIDATION_PROTOCOL_V1.md
- docs/A3_ML_POWER_MDE_PROTOCOL_V1.md
- docs/A3_ML_DETERMINISTIC_BENCHMARK_PROTOCOL_V1.md
- docs/A3_ML_MODEL_SELECTION_PROTOCOL_V1.md
- docs/A3_ML_SHADOW_GOVERNANCE_V1.md
- docs/A3_ML_RETRAINING_POLICY_V1.md
- docs/A3_ML_OWNER_TIMELINE_EXPECTATION_V1.md

Added contract-structure tests for:

- ownership and required contract set;
- holding-horizon sensitivity governance;
- feature budget and fold diagnostics;
- direction asymmetry and interaction scope;
- shadow-only safety clauses.

## Tests Run

Pytest was attempted with the bundled Python runtime but was unavailable:

```text
No module named pytest
```

The new test functions were then executed with a direct import/assertion harness using the bundled Python runtime.

Result:

```text
contract test functions run: 24
all contract test functions passed
```

No model code was executed.

## Next Permitted Task

After contract tests pass, proceed to C01 pre-lock verification and manifest. Do not train a model.
