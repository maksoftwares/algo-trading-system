# REVIEW — A3 Python ML Signal-Quality Spec

**Spec under review:** `CODEX_A3_PYTHON_ML_SIGNAL_QUALITY_SPEC_2026_06_20.md`
**Review date:** 2026-06-21
**Scope:** Design soundness, statistical validity, leakage safety, implementation risk
**Severity legend:** **[H]** must fix before locking contracts (ML-01) · **[M]** fix before candidate evaluation · **[L]** improvement / nice-to-have

---

## Verdict

Approve the architecture and safety model; do not lock contracts (ML-01) until the High-severity items below are resolved. This is a well-disciplined spec — the framing is correct and the governance is unusually strong. The remaining risks are almost entirely **statistical**, not conceptual: feature-to-sample ratio, the statistical power of the pass/value gates, two subtle leakage paths, and label realism. None require rethinking the approach; they require tightening parameters and definitions before the contracts are hash-locked.

---

## What is sound (preserve through revisions)

These choices are correct and should not regress in any rewrite:

- **Meta-labeling as the first use.** The deterministic engine retains direction, entry, stop, 1.50R target, lot, risk, and account; ML only ranks signal quality. This is the lowest-risk, most-validatable application.
- **Labeling all would-signals counterfactually** (§3), not just executed trades — correctly removes the selection/survivorship bias that would otherwise dominate.
- **Purged expanding walk-forward with embargo and signal-group integrity** (§15) — the right validation scheme for overlapping-label data; refusing random shuffling is correct.
- **Pre-registration of models, grids, thresholds, and gates before viewing results** (§16, §18, §21) — the single strongest defense against forking-path / multiple-comparison overfitting.
- **Calibration as a first-class output** (§17) with sigmoid/isotonic gated by sample size, and Brier-skill vs a base-rate model.
- **Three weeks treated as discovery data, not holdout** (§2, §22); fresh locked forward window required.
- **Hash-locked contracts, model registry, no mutable filenames, reproducibility manifest** (§5, §25) — strong MLOps hygiene.
- **Concentration and block-bootstrap CI requirements** (§19.4, §21) — correctly guards against a few trades carrying the result.

---

## Priority findings

### 1. [H] Feature count is too high for the sample-size gates

**Issue.** V1 caps at 35 features (§10), but the dataset gates admit modeling at ~75 minority events (EXPLORATORY, §14.2) and candidate evaluation at ~200 (§14.3). At a standard 10–20 events-per-variable rule, 75 events supports roughly 4–7 features and 200 supports roughly 10–20 — not 35.

**Why it matters.** All the leakage discipline is wasted if the model overfits on dimensionality. This is the largest under-weighted risk in the spec; it currently receives far less attention than leakage.

**Recommendation.** Tie the feature budget to events, not a fixed cap (e.g., `max_features ≤ minority_events / 15`). Strengthen the logistic `C` grid toward more regularization — add `0.01`; `10.0` is very weak for this n/p regime (§16.2). Consider a pre-registered L1 or stability-selection step inside the CV. Drop or down-weight low-value categoricals that spend scarce parameters (see §7 below).

**Spec refs:** §10, §14.2, §14.3, §16.2

### 2. [H] Pass and incremental-value gates are not statistically powered

**Issue.** Gates such as PF ≥ 1.30 and expectancy ≥ +0.15R (§21) are stated as point thresholds, and the ML-vs-rule gate is +0.03R / +0.10 PF (§20). The forward minimum is ~100 trades (§22.2). On 100 trades a PF point estimate has a confidence interval roughly spanning 0.9–2.0, and a 0.03R edge is below the noise floor — detecting a ~0.03R mean difference at per-trade R std ≈ 1.1 needs on the order of 10³–10⁴ trades; even the paired/nested nature of the comparison does not rescue 100.

**Why it matters.** As written, pass/fail on the forward window will be decided largely by noise, and "ML materially beats the rule" cannot be confirmed at the specified sample size.

**Recommendation.** Restate the gates as confidence-bound conditions (e.g., bootstrap 5th-percentile PF > 1.0 **and** point PF ≥ 1.30) rather than bare point thresholds. Use the larger OOS walk-forward sample as the primary venue for the ML-vs-deterministic comparison; treat the small forward window as confirmation, not discovery. Add an explicit power / minimum-detectable-effect calculation to the validation protocol, and accept that confirming the edge is a multi-quarter evidence-accumulation exercise.

**Spec refs:** §19.4, §20, §21, §22.2

### 3. [H] Two leakage paths the leakage section may not catch

**Issue A — rolling-percentile / normalization features.** `m5_atr_percentile_20d`, `spread_percentile_session_20d`, `h1_atr_percentile_60d` (§10.3) are computed in `features.py`, not as preprocessors. The "fit preprocessors on the training fold only" rule (§15) governs the scaler/imputer but may not reach these. If any percentile reference distribution is full-sample, that is look-ahead leakage.

**Issue B — near-duplicate setups across lanes.** Dedup relies on an exact `signal_id` hash (§8). The same setup emitted by 933200/933300/933400 with slight timing jitter (different confirmation timestamps) will not collapse to one ID, will survive as near-duplicates, and can then split across train/test folds — leaking information across the walk-forward boundary.

**Recommendation.** (A) Require all percentile/normalization statistics to be trailing-only and computed within the training fold; add a leakage test that fails on full-sample statistics. (B) Add a fuzzy dedup pass on top of the hash — collapse signals with the same direction and level within X·ATR and overlapping time windows into one group before splitting.

**Spec refs:** §8, §9, §10.3, §15, §28 (Data tests)

### 4. [H] Label realism: undefined timeout and unmodeled slippage

**Issue.** The holding-horizon / timeout behavior is still undefined — the spec itself flags this as a stop condition (§12). Separately, virtual fills model spread but not slippage beyond spread (§7, §12). Labels are ground truth for everything downstream, so bias here propagates into every metric and gate.

**Why it matters.** Timeout policy sets the win/loss/timeout proportions and the embargo length, so none of the sample-size gates are meaningful until it is fixed. For XAUUSD specifically, SL slippage around US data releases and the London/NY opens is material; modeling it optimistically biases expectancy high everywhere.

**Recommendation.** Resolve and hash-lock the timeout/holding-horizon addendum **first**, before dataset construction (as §12 already requires). Add conservative SL-side slippage to the virtual-execution contract, or document and bound the optimism if it is omitted.

**Spec refs:** §7, §12

### 5. [M] Regime coverage is gated but the regime classifier is not pre-registered

**Issue.** Multiple gates require "rising / falling / mixed" regime coverage (§14.3, §21, §22.2), but no deterministic regime definition is registered. Deciding regime post hoc is a researcher degree of freedom that makes the coverage gate unfalsifiable.

**Recommendation.** Commit a deterministic, pre-registered regime classifier in the data contract (e.g., D1 EMA slope sign and/or ADX bands), so regime coverage is an objective check.

**Spec refs:** §14.3, §21, §22.2

### 6. [M] The deterministic benchmark may be an unfair comparison

**Issue.** The ML model is selected over a grid via CV, while the deterministic baselines (`F_LOOSE_CT_VETO`, `F_H1_ALIGN`, `F_RETEST_LIGHT`, §20) appear fixed and untuned. This biases the "ML wins" outcome — ML got to pick its best configuration OOS; the rules did not.

**Recommendation.** Give the deterministic rules the same small pre-registered parameter search under the same CV, or require ML to clear the value gate by a wider margin to offset the selection advantage.

**Spec refs:** §16.4, §20

### 7. [L] Objective mismatch and parameter-spend nits

- **Brier vs expectancy.** Model selection uses validation Brier (§16.2); the business objective is expectancy/PF at the chosen threshold. With asymmetric 1.5R/1R payoffs and timeouts, better Brier does not guarantee better expectancy at the operating point. Add expectancy-at-threshold as a pre-registered secondary selection criterion.
- **Binary `net_R > 0`** (§12) discards magnitude. Keep leaning on `y_net_R` and the decile-expectancy check (§19.3) so ranking tracks expected R, not just P(win).
- **`day_of_week` one-hot** (§10.4) spends scarce parameters on a weak, unstable effect; drop or strongly regularize given finding #1.

**Spec refs:** §10.4, §12, §16.2, §18, §19.3

---

## Pre-lock action checklist (before ML-01 hash-lock)

1. Resolve and hash-lock the timeout/holding-horizon addendum; add SL slippage to the execution contract. *(Finding 4)*
2. Replace the fixed 35-feature cap with an events-based budget; strengthen the `C` grid; trim low-value categoricals. *(Findings 1, 7)*
3. Restate §21 / §20 gates as bootstrap confidence-bound conditions; add a power / MDE calculation to the validation protocol; designate OOS walk-forward as the primary comparison venue. *(Finding 2)*
4. Add trailing-/train-fold-only enforcement and a test for percentile features; add a fuzzy cross-lane dedup pass. *(Finding 3)*
5. Register a deterministic regime classifier in the data contract. *(Finding 5)*
6. Give deterministic baselines an equivalent pre-registered search, or widen the ML value margin. *(Finding 6)*

Findings 1–4 should be closed before contracts are locked; 5–6 before candidate evaluation (ML-07 onward).

---

## Bottom line

The plan is sound enough to build on its current `ML-00 → ML-14` spine. Tighten the feature-to-sample ratio, re-express the gates as powered confidence bounds, close the two leakage paths, and fix the label contract (timeout + slippage) before ML-01 locks anything. Those four are what separate this passing from passing *for real*.
