# CODEX FINAL PRE-LOCK MERGE PACKET — A3 Python ML V1.2

**Project:** `maksoftwares/algo-trading-system`  
**Date:** 2026-06-21  
**Supersedes sequencing guidance in:**  
- `CODEX_A3_PYTHON_ML_SIGNAL_QUALITY_SPEC_V1_1_2026_06_21.md`
- `CODEX_A3_PYTHON_ML_SPEC_V1_2_PRELOCK_ADDENDUM_2026_06_21.md`

**Incorporates:**  
- `A3_ML_V1_2_PRELOCK_CLARIFICATIONS_DROPIN_2026_06_21.md`

**Scope:** A3 / account `1033669`, XAUUSD, breakout-retest meta-labeling  
**Runtime:** repo-only / shadow-only  
**Broker action:** prohibited  
**A3 state:** `933200`, `933300`, `933400` remain paused; profit-lock remains dry-run/disarmed  

---

# 1. Final verdict

```text
V1.2 architecture:                 APPROVED
Pre-lock clarifications:           NON-BLOCKING / MUST MERGE
ML-00 inventory:                   GO
ML-00A contract merge:             GO
ML-01 hash-lock:                   GO after merge verification
Model training before ML-01:       NO-GO
A3 broker action:                  NO-GO
```

The reviewer has no remaining open findings after the three clarifications below are merged into the final hashed contracts.

---

# 2. Single-source-of-truth rule

Before ML-01:

1. Merge every V1.2 addendum clause into its final owning contract.
2. Hash the final merged contract files.
3. Retain the addendum and review files only as revision history.
4. Do not treat the addendum as a parallel runtime contract.
5. No clause may exist only in an addendum after ML-01.

The runtime/research source of truth is the set of files recorded in:

```text
outputs/manifests/A3_ML_V1_LOCK_MANIFEST.json
```

---

# 3. Clarification V1 — Holding-horizon change governance

## Target

Insert into:

```text
docs/A3_ML_EXECUTION_LABEL_CONTRACT_V1.md
```

Add a cross-reference in:

```text
docs/A3_ML_FEATURE_BUDGET_CONTRACT_V1.md
```

## Contract text

```text
# Holding-horizon change governance

The holding horizon is a trading-product parameter, not a model-capacity
parameter. The locked primary horizon is 288 active M5 bars.

The horizon-sensitivity table is mechanics-only and informational.

A holding-horizon change is permitted only when ALL hold:

1. The rationale is stated in trade-economics terms
   (exposure window, target/stop geometry, session and overnight risk,
   signal decay), independent of model capacity.
2. The rationale does not cite implied feature budget, feature count,
   or model capacity as a reason.
3. A new versioned label contract, new review, and new SHA256 lock
   are produced.

Explicitly prohibited:

- shortening the horizon because a shorter horizon yields a larger
  global_feature_budget;
- shortening the horizon in order to admit more features;
- selecting the horizon from any outcome metric
  (PF, expectancy, win rate, score, threshold).

A larger implied feature budget is never, by itself, a valid reason
to change the holding horizon.
```

## Feature-budget cross-reference

```text
The holding horizon is fixed by the execution label contract and may not
be changed to enlarge global_feature_budget. See "Holding-horizon change
governance" in A3_ML_EXECUTION_LABEL_CONTRACT_V1.md.
```

## Required tests

```text
test_horizon_change_cannot_reference_feature_budget
test_horizon_change_requires_new_contract_version
test_horizon_sensitivity_is_mechanics_only
test_horizon_sensitivity_contains_no_outcome_metrics
```

---

# 4. Clarification V2 — Direction-interaction admission does not relax pass gates

## Target

Insert into:

```text
docs/A3_ML_MODEL_SELECTION_PROTOCOL_V1.md
```

Also cross-reference from:

```text
docs/A3_ML_DIRECTION_ASYMMETRY_PROTOCOL_V1.md
```

## Contract text

```text
# Scope of direction-interaction admission

Admission of M1_LOGISTIC_L2_DIRINT is a model-selection step performed
on inner-OOF data only. It does not modify any downstream gate.

Whichever model is selected — M1_LOGISTIC_L2_SYMMETRIC or
M1_LOGISTIC_L2_DIRINT — must clear, unchanged, all absolute and
incremental candidate gates on P95-stress labels.

Absolute gates:

  point PF >= 1.30
  AND PF 5th percentile > 1.00

  point expectancy / retained trade >= +0.15R
  AND expectancy 5th percentile > 0R

  point expectancy / raw base signal > 0R
  AND raw-signal expectancy 5th percentile > 0R

Incremental versus the selected deterministic rule:

  point delta_R / raw base signal > 0
  AND delta_R 5th percentile > 0

  AND either:
    point expectancy improvement >= +0.03R
    OR point PF improvement >= +0.10

The +0.01R inner-OOF improvement criterion governs only whether the
interaction model is preferred over the symmetric model during
selection.

It does not lower, waive, or substitute for any final candidate gate.

If the selected model fails any final gate:
  resolve as CONTINUE_EVIDENCE or NO-GO under the existing protocol.
```

## Required tests

```text
test_direction_interaction_does_not_change_absolute_gates
test_direction_interaction_does_not_change_incremental_gates
test_inner_selection_gain_cannot_authorize_candidate
test_selected_interaction_model_still_uses_p95_stress_gates
```

---

# 5. Clarification V3 — Merge and lock hygiene

## Test-file correction

The following file already exists and must be updated, not added:

```text
tests/test_a3_ml_feature_budget.py
```

New files:

```text
tests/test_a3_ml_direction_asymmetry.py
tests/test_a3_ml_fold_diagnostics.py
tests/test_a3_ml_horizon_sensitivity.py
```

Updated file:

```text
tests/test_a3_ml_feature_budget.py
```

## Final contract ownership map

Before ML-01, ensure the following ownership:

```text
docs/A3_ML_DIRECTION_ASYMMETRY_PROTOCOL_V1.md
  owns:
    direction diagnostics
    asymmetry gate
    one conditional interaction
    sample adequacy
    fold-consistency rules

docs/A3_ML_FEATURE_BUDGET_CONTRACT_V1.md
  owns:
    post-calibration minority count
    global feature budget
    per-fold diagnostics
    binding-fold rule
    horizon governance cross-reference

docs/A3_ML_OWNER_TIMELINE_EXPECTATION_V1.md
  owns:
    multi-month evidence expectation
    CONTINUE_EVIDENCE semantics
    no schedule-based gate relaxation

docs/A3_ML_EXECUTION_LABEL_CONTRACT_V1.md
  owns:
    288-active-M5-bar horizon
    entry expiry
    timeout
    gap handling
    slippage labels
    holding-horizon change governance

docs/A3_ML_VALIDATION_PROTOCOL_V1.md
  owns:
    long/short OOS diagnostics
    purge/embargo
    calibration split
    fold diagnostics
    forward evidence rules

docs/A3_ML_MODEL_SELECTION_PROTOCOL_V1.md
  owns:
    symmetric versus interaction selection
    inner-OOF admission
    final absolute/incremental gates
    deterministic benchmark comparison

docs/A3_ML_DATA_CONTRACT_V1.md
  owns:
    fuzzy grouping
    feature-time ordering
    trainable labels
    per-fold class-count schema
    data-audit schema
```

## Manifest policy header

Add to:

```text
outputs/manifests/A3_ML_V1_LOCK_MANIFEST.json
```

Policy:

```text
All V1.2 addendum and clarification clauses have been merged into their
final owning contract files before hashing.

The addendum and review files are retained as revision history only.

No runtime or research rule may be sourced solely from an un-hashed
addendum after this manifest is created.
```

---

# 6. Final ML-00A merge checklist

Codex must verify every item before hashing.

```text
[ ] Holding-horizon governance inserted into execution label contract.
[ ] Feature-budget cross-reference inserted.
[ ] Direction-interaction scope inserted into model-selection contract.
[ ] Direction-asymmetry protocol cross-references final gates.
[ ] Post-calibration minority count definition inserted.
[ ] Per-fold purge/calibration/budget diagnostics inserted.
[ ] Owner timeline / CONTINUE_EVIDENCE contract inserted.
[ ] Existing feature-budget test marked UPDATED, not NEW.
[ ] All new tests added.
[ ] Every addendum clause exists in a final contract.
[ ] No conflicting duplicate wording remains.
[ ] No final threshold changed.
[ ] No 288-bar horizon change.
[ ] No extra direction interaction added.
[ ] No separate long/short model introduced.
[ ] A3 pause remains unchanged.
[ ] Full test suite passes.
```

---

# 7. Hash-lock procedure

After merge:

1. Normalize files exactly as the repository’s existing hash convention requires.
2. Compute SHA256 for every final contract file.
3. Record:
   - relative path;
   - SHA256;
   - file size;
   - created/locked UTC;
   - source commit;
   - contract role.
4. Verify hashes with an independent script.
5. Run the complete test suite.
6. Commit contracts and manifest together.
7. Do not amend any locked contract afterward.
8. Any required change creates:
   - new contract version;
   - new manifest;
   - new review.

Suggested manifest entries:

```text
A3_ML_META_LABEL_HYPOTHESIS_V1.md
A3_ML_DATA_CONTRACT_V1.md
A3_ML_SIGNAL_GROUPING_CONTRACT_V1.md
A3_ML_EXECUTION_LABEL_CONTRACT_V1.md
A3_ML_SLIPPAGE_MODEL_CONTRACT_V1.md
A3_ML_FEATURE_REGISTRY_V1.csv
A3_ML_FEATURE_BUDGET_CONTRACT_V1.md
A3_ML_REGIME_CONTRACT_V1.md
A3_ML_DIRECTION_ASYMMETRY_PROTOCOL_V1.md
A3_ML_VALIDATION_PROTOCOL_V1.md
A3_ML_POWER_MDE_PROTOCOL_V1.md
A3_ML_DETERMINISTIC_BENCHMARK_PROTOCOL_V1.md
A3_ML_MODEL_SELECTION_PROTOCOL_V1.md
A3_ML_SHADOW_GOVERNANCE_V1.md
A3_ML_RETRAINING_POLICY_V1.md
A3_ML_OWNER_TIMELINE_EXPECTATION_V1.md
```

---

# 8. Required pre-lock verification report

Generate:

```text
outputs/ml/a3_meta_v1/reports/
  A3_ML_V1_PRELOCK_MERGE_VERIFICATION.md
  A3_ML_V1_PRELOCK_MERGE_VERIFICATION.json
```

Required fields:

```text
status
source_commit
contract_count
manifest_path
all_hashes_match
all_addendum_clauses_merged
unmerged_clause_count
duplicate_conflict_count
test_result
A3_runtime_authorization
A3_open_positions
A3_pending_orders
broker_action_changed
```

Passing values:

```text
status = PASS
all_hashes_match = true
all_addendum_clauses_merged = true
unmerged_clause_count = 0
duplicate_conflict_count = 0
A3_runtime_authorization = A3_ENTRY_LANES_PAUSED
A3_open_positions = 0
A3_pending_orders = 0
broker_action_changed = false
```

---

# 9. ML-01 gate

ML-01 may start only when:

```text
pre-lock merge verification PASS
all contract hashes recorded
all tests green
A3 remains paused
no broker-action files changed
no armed preset/profile committed
```

ML-01 may:

```text
lock contracts
generate manifests
record environment
prepare ML-00 inventory implementation
```

ML-01 may not:

```text
train a model
select a feature
calculate a threshold
inspect final forward outcomes
attach a shadow scorer
```

---

# 10. Final status

```text
Pre-lock architecture:        APPROVED
Clarifications:               MERGE REQUIRED
Outstanding review blockers: NONE
Contract hash-lock:           GO after merge verification
Model training:               NOT YET
A3 broker action:             NO-GO
```

A3 remains paused throughout.
