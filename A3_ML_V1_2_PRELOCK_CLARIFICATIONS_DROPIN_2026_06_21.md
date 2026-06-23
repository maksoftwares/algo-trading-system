# DROP-IN CONTRACT TEXT — V1.2 Pre-Lock Clarifications

**For:** planner / Codex, to fold into the V1.2 contract set before ML-01 hash-lock
**Source:** `A3_ML_SPEC_V1_2_PRELOCK_ADDENDUM_REVIEW_2026_06_21.md` (observations V1, V2, V3)
**Date:** 2026-06-21
**Status:** all three are non-blocking; insert during the merge, then hash the merged contracts

Each block below is ready to paste. Style matches the existing contracts. Target file and insertion point are noted above each block.

---

## V1 — Holding-horizon change governance

**Target:** `docs/A3_ML_EXECUTION_LABEL_CONTRACT_V1.md` (owns the 288-bar horizon)
**Cross-reference:** add a one-line pointer from `docs/A3_ML_FEATURE_BUDGET_CONTRACT_V1.md`
**Why:** the V1.2 §7 horizon-sensitivity table reports *implied feature budget*; a shorter horizon mechanically yields a larger budget, creating a capacity-driven pressure to shorten the horizon that the existing "no outcome metrics" guard does not cover.

```text
# Holding-horizon change governance

The holding horizon is a trading-product parameter, not a model-capacity
parameter. The locked primary horizon is 288 active M5 bars.

The horizon-sensitivity table (V1.2 §7) is mechanics-only and informational.

A holding-horizon change is permitted only when ALL hold:

1. The rationale is stated in trade-economics terms
   (exposure window, target/stop geometry, session and overnight risk,
   signal decay), independent of model capacity.
2. The rationale does not cite implied feature budget, feature count,
   or model capacity as a reason.
3. A new versioned label contract, new review, and new SHA256 lock
   are produced per V1.2 §7.

Explicitly prohibited:

- shortening the horizon because a shorter horizon yields a larger
  global_feature_budget;
- shortening the horizon in order to admit more features;
- selecting the horizon from any outcome metric
  (PF, expectancy, win rate, score, threshold).

A larger implied feature budget is never, by itself, a valid reason
to change the holding horizon.
```

Cross-reference line for the feature-budget contract:

```text
The holding horizon is fixed by the execution label contract and may not
be changed to enlarge global_feature_budget. See "Holding-horizon change
governance" in A3_ML_EXECUTION_LABEL_CONTRACT_V1.md.
```

---

## V2 — Scope of direction-interaction admission

**Target:** `docs/A3_ML_MODEL_SELECTION_PROTOCOL_V1.md` (and/or the §3.6 block of `A3_ML_DIRECTION_ASYMMETRY_PROTOCOL_V1.md`)
**Why:** the +0.01R inner-OOF bar in V1.2 §3.6 is a lenient *selection* heuristic; this clause states plainly that admitting the interaction never relaxes the V1.1 §31 outer gates.

```text
# Scope of direction-interaction admission

Admission of M1_LOGISTIC_L2_DIRINT (V1.2 §3.3–§3.6) is a model-selection
step performed on inner-OOF data only. It does not modify any downstream gate.

Whichever model is selected — M1_LOGISTIC_L2_SYMMETRIC or
M1_LOGISTIC_L2_DIRINT — must clear, unchanged, all V1.1 §31 gates on
P95-stress labels:

  absolute:
    point PF >= 1.30                          AND PF 5th percentile > 1.00
    point expectancy / retained trade >= +0.15R AND 5th percentile > 0R
    point expectancy / raw base signal > 0R     AND 5th percentile > 0R

  incremental vs selected deterministic rule:
    point delta_R / raw base signal > 0       AND delta_R 5th percentile > 0
    AND ( point expectancy improvement >= +0.03R
          OR point PF improvement >= +0.10 )

The +0.01R inner-OOF improvement bar in §3.6 governs only whether the
interaction model is preferred over the symmetric model during selection.
It does not lower, waive, or substitute for any §31 threshold.

If the selected model (with or without the interaction) fails §31:
  resolve as CONTINUE_EVIDENCE or NO-GO per existing rules.
```

---

## V3 — Merge and lock hygiene

**Target:** `ML-00A` instructions and the policy header of `outputs/manifests/A3_ML_V1_LOCK_MANIFEST.json`
**Why:** V1.2 §2 lists an already-existing test under "Add," and the addendum should not persist as a parallel runtime contract once merged.

```text
# Merge and lock hygiene (V1.2 incorporation)

1. Test-file correction.
   tests/test_a3_ml_feature_budget.py already exists in the V1.1 layout;
   V1.2 UPDATES it, it is not new.

   New in V1.2:
     tests/test_a3_ml_direction_asymmetry.py
     tests/test_a3_ml_fold_diagnostics.py
     tests/test_a3_ml_horizon_sensitivity.py

   Updated in V1.2:
     tests/test_a3_ml_feature_budget.py

2. Single source of truth.
   Before ML-01, fold the addendum content into hashed contract files:

     A3_ML_DIRECTION_ASYMMETRY_PROTOCOL_V1.md   new, standalone
     A3_ML_FEATURE_BUDGET_CONTRACT_V1.md        new, standalone (incl. V1 cross-ref)
     A3_ML_OWNER_TIMELINE_EXPECTATION_V1.md     new, standalone
     A3_ML_EXECUTION_LABEL_CONTRACT_V1.md       absorb V1 horizon governance
     A3_ML_VALIDATION_PROTOCOL_V1.md            absorb §3.2 diagnostics
     A3_ML_MODEL_SELECTION_PROTOCOL_V1.md       absorb §3.6 and the V2 clause
     A3_ML_DATA_CONTRACT_V1.md                  absorb §4–§6 budget/fold diagnostics

3. The lock manifest records the SHA256 of each final merged contract file.
   The V1.2 addendum is retained only as revision history and is NOT a
   runtime contract once merged. No clause may exist in the addendum
   without also existing in a hashed contract file.
```

---

## After insertion

Once V1–V3 are merged and the contracts are hashed, the pre-lock checklist is complete: proceed ML-00 → ML-00A → ML-01, A3 paused throughout. No further review items are open from my side.
