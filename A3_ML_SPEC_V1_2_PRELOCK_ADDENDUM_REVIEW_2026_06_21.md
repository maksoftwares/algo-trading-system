# REVIEW — A3 Python ML Spec **V1.2 Pre-Lock Addendum**

**Addendum under review:** `CODEX_A3_PYTHON_ML_SPEC_V1_2_PRELOCK_ADDENDUM_2026_06_21.md`
**Base spec:** `CODEX_A3_PYTHON_ML_SIGNAL_QUALITY_SPEC_V1_1_2026_06_21.md`
**Prior reviews:** `A3_ML_SIGNAL_QUALITY_SPEC_REVIEW_2026_06_21.md`, `A3_ML_SIGNAL_QUALITY_SPEC_V1_1_REVIEW_2026_06_21.md`
**Review date:** 2026-06-21
**Severity legend:** **[H]** blocker · **[M]** fix before candidate eval · **[L]** improvement · **[i]** informational

---

## Verdict

**Cleared to hash-lock.** The addendum resolves both pre-lock edits and the two supporting observations from the V1.1 review, with rigor beyond what was requested. There are no blockers and no open Medium items. Proceed: ML-00 inventory → ML-00A → ML-01, A3 paused throughout. The three new notes below are minor and can be folded in during the merge or left as-is.

---

## Disposition of V1.1 observations

**N1 (direction symmetry) — CLOSED / exceeded.** §3 is a complete protocol that does exactly what was asked and firewalls it correctly:

- The pooled symmetric model stays primary; separate long/short models remain prohibited (§3.1).
- A per-direction **diagnostic** runs on outer-test predictions as reporting-only, explicitly barred from selecting the same fold's model (§3.2) — so the symmetry assumption is monitored from the first fold even before any repair is eligible.
- The **repair** is gated on asymmetry *demonstrated on inner OOF data only* (sample minimums, pre-registered effect thresholds, sign-consistency across inner folds, a 90% bootstrap CI excluding zero), keeping the outer test clean (§3.3).
- I checked the interaction algebra and it is correct. With `aligned = sign·x` (x = raw H1 slope), the term `h1_slope_direction_interaction = sign·aligned = x`. Including both lets the slope effect be `(b_aligned + b_int)` for longs and `(b_int − b_aligned)` for shorts — i.e. one extra coefficient buys a direction-specific slope sensitivity, equivalent to adding the raw unaligned slope. It is the minimal correct decoupling, and item 1 (the aligned slope) is always in the prefix, so the dependency is guaranteed (§3.4).
- Capacity is honest: the term counts against the budget and, if the budget is full, displaces the lowest-priority base feature deterministically — and the swap is only made if the interaction model wins the inner head-to-head (Brier not worse, expectancy up ≥0.01R, neither direction down >0.02R), with symmetric winning ties (§3.5–§3.6). It is not auto-preferred just because asymmetry exists.

**N3 (budget timing) — CLOSED.** §4.1 specifies the exact 8-step ordering and defines `minority_events_min` as the post-grouping, post-purge, post-embargo, post-unresolved-removal, **post-calibration-split** model-fit minority, minimised across outer folds. The ambiguity is gone.

**N2 (earliest-fold / horizon interaction) — CLOSED / exceeded.** §5 mandates a per-fold purge/calibration/class-count/budget schema in the audit and split manifest and names the binding fold. §6 sets an explicit anti-gaming starvation policy (report what binds; don't drop the earliest fold, add future data, or use larger prefixes in later folds). §7 turns the holding-horizon into a **mechanics-only** sensitivity table (96/144/288 bars) that may report sample counts and implied budget but is forbidden from reporting PF/expectancy/win-rate/score/threshold — which neatly prevents outcome-driven horizon selection, and any change still requires a new versioned, reviewed, re-locked contract.

**N4 (timeline expectation) — CLOSED / exceeded.** §9 documents the multi-month cadence, defines `CONTINUE_EVIDENCE` as "operating correctly but sample too weak," and hardens it into governance: schedule pressure may not convert it to PASS, and no deadline may override sample/MDE/confidence/regime gates (also added to NO-GO in §11).

---

## New observations on V1.2 (none blocking)

**V1. [L] The horizon-sensitivity table exposes "implied feature budget," which is itself a selection pressure.** §7 correctly bans outcome metrics, but a shorter horizon mechanically means less purge → larger budget → more model capacity. That is a capacity-driven temptation, not an outcome-driven one, so it slips past the existing guard. Recommend the feature-budget/label contract state explicitly that a holding-horizon change must be justified on **trade-economics** grounds, and that a larger implied feature budget is not by itself a valid reason to shorten the horizon. The horizon defines the trading product; it should not be chosen to feed the model.

**V2. [L] The interaction-admission inner bar (+0.01R) is lenient — confirm it never relaxes the outer gates.** A 0.01R inner-OOF improvement is small, but it is backstopped by the independent asymmetry CI gate (§3.3) and, crucially, the final model including the interaction must still clear the V1.1 §31 outer confidence-bound gates. Worth one line in the model-selection contract stating that interaction admission is a selection step only and never alters the §31 absolute/incremental gates.

**V3. [i] Housekeeping at merge.** §2 lists `tests/test_a3_ml_feature_budget.py` under "Add tests," but it already exists in the V1.1 layout — it is an update, not a new file. More importantly, fold the three new docs into the existing contracts and hash the **merged** contracts in the lock manifest, so there is a single source of truth rather than an addendum living in parallel with the base spec.

---

## Bottom line

V1.2 closes the last two pre-lock items and the supporting diagnostics, and the one piece of new machinery — the conditional direction-interaction term — is mathematically sound and properly leakage-firewalled. Lock the contracts (ML-00A / ML-01) and proceed to ML-00 inventory. Optionally add the two one-line clarifications above (V1, V2) during the merge; V3 is pure housekeeping. A3 remains paused, and the program's terminal states correctly include `CONTINUE_EVIDENCE`.
