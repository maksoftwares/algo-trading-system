# REVIEW — A3 Python ML Signal-Quality Spec **V1.1**

**Spec under review:** `CODEX_A3_PYTHON_ML_SIGNAL_QUALITY_SPEC_V1_1_2026_06_21.md`
**Supersedes:** `CODEX_A3_PYTHON_ML_SIGNAL_QUALITY_SPEC_2026_06_20.md`
**Prior review:** `A3_ML_SIGNAL_QUALITY_SPEC_REVIEW_2026_06_21.md`
**Review date:** 2026-06-21
**Severity legend:** **[H]** blocker · **[M]** fix before candidate evaluation · **[L]** improvement / clarification · **[i]** informational

---

## Verdict

**Cleared to proceed to contract hash-lock (ML-00A → ML-01).** All seven findings from the first review are closed — four of them (the High-severity items) are not just patched but addressed more thoroughly than the original review asked. The new observations below are modeling-judgment and clarification items; **none is a blocker** and none should hold up locking.

The revision is internally consistent: the dataset eligibility tiers, feature-budget rule, slippage adequacy, and confidence-bound gates all reference each other coherently, and the numeric thresholds line up (e.g., minority ≥240 → events/15 ≈ 16 features at candidate tier).

---

## Disposition of prior findings

**1. [H] Feature count vs sample size — CLOSED.** The fixed 35-cap is removed (§18). Budget is now `min(16, floor(minority_events_min / 15))` computed on the *minimum* minority count across outer folds, with a pre-registered ordered feature list of 16 numeric features (§19), budget gates per tier (§22), and `<5 → PIPELINE_ONLY`. C grid tightened to 0.01/0.10/1.00 and `C=10.0` removed (§25.2). This is exactly the events-per-variable discipline recommended, and counting *effective* transformed columns incl. missing indicators (§18.1, §20) shows the parameter-count point landed.

**2. [H] Gates not statistically powered — CLOSED / exceeded.** New §30 (power & MDE), §31 (confidence-bound gates), §36 (CIs). Absolute gates now require point **and** bootstrap 5th-percentile bounds (PF ≥1.30 *and* 5th pct >1.00, etc.). The incremental gate adds a paired `delta_R` per raw base signal with a lower-bound condition and a `CONTINUE_EVIDENCE` state for underpowered evidence (§31.2). Historical purged OOS is explicitly designated the primary comparison venue and the ~100-trade forward window is demoted to an implementation/drift checkpoint that "cannot by itself prove a +0.03R edge" (§32.2), with a separate, MDE-gated forward *confirmation* minimum (§32.3). The paired-delta design (skips contribute zero, §30.1) is a genuinely strong addition — by zeroing agreements it cuts the comparison's variance, which materially improves the power situation beyond what my original note assumed.

**3. [H] Two leakage paths — CLOSED / exceeded.** Rolling percentiles are now causal/trailing with a current-row exclusion (§17.2), backed by a general **prefix-invariance test** (§17.1, §24) that is stronger than the percentile-specific guard I suggested. Near-duplicate setups are handled by a full fuzzy-grouping algorithm with `setup_group_id`, connected-component logic, a 20-minute span cap, ATR sensitivity bands, and a "cannot cross train/test" rule (§11, §23).

**4. [H] Label realism — CLOSED / exceeded.** Execution contract now locks a 288-active-bar (24 active-hour) timeout, entry expiry, quote-side, and gap handling (§13). An empirical slippage model (§14) is built from real fills with adequacy gates, **expected (P50) and P95-stress label scenarios**, candidate gates required to pass under P95 stress, and per-fold causal fitting of the slippage distribution (§14.5) — which also closes a slippage-leakage path the first review didn't separately flag.

**5. [M] Regime classifier not pre-registered — CLOSED.** Deterministic D1 rule registered in §21 / `A3_ML_REGIME_CONTRACT_V1.md`, with an `UNKNOWN` state excluded from coverage.

**6. [M] Unfair deterministic benchmark — CLOSED.** §29 gives each rule (`D_LOOSE_CT_VETO`, `D_H1_ALIGN`, `D_RETEST_LIGHT`) a pre-registered grid and the same nested-CV selection and eligibility as the model.

**7. [L] Selection mismatch + nits — CLOSED.** §26 selects within one SE of best Brier, then by expectancy at a retention-valid threshold (the Brier-primary/expectancy-aligned rule recommended). `day_of_week`, lane, magic, and raw one-hots removed from V1 (§19); both `y_net_R_expected` and `y_net_R_p95_stress` retained (§15).

---

## New observations on V1.1 (none blocking)

**N1. [M] Direction-normalization assumes long/short symmetry.** All signed features are multiplied by `direction_sign` and pooled into one model (§19). This doubles effective sample per coefficient and is the right parsimony move, but it bakes in the assumption that the feature→quality relationship is symmetric across longs and shorts — which is not obviously true for XAUUSD (sell-offs and grind-ups behave differently). Long/short *trading* metrics (§34) and direction-mix drift (§42) are tracked, but neither tests the symmetry of the *learned relationship*. Recommend adding a direction-asymmetry diagnostic to the validation protocol: compare per-direction calibration slope/intercept and OOS Brier, and pre-register a single direction-interaction term to be admitted only if asymmetry is demonstrated. This belongs in the validation protocol before ML-01 lock, but does not block the lock itself.

**N2. [L] Feature budget is bound by the earliest expanding fold, and interacts with the 24-hour label horizon.** `minority_events_min` is the minimum across outer training folds (§18.2); in expanding walk-forward that is fold 1, so the thinnest early fold caps the feature budget everywhere. The 288-active-bar horizon (§13.4) compounds this: long labels mean the purge (§23) removes more training rows near fold boundaries, further shrinking the minority count that sets the budget. Net effect to watch in ML-00/ML-03: the model may be capped to few features even when later folds are data-rich, and adding *earlier* history could paradoxically lower the budget. Recommend the data audit report per-fold minority counts, purge loss, and the resulting budget, and treat the holding horizon as an available lever if the budget comes out starved.

**N3. [L / clarify] Define when the budget's minority count is measured.** §23 carves a disjoint calibration tail out of each training block; §18.2 doesn't state whether `minority_events_min` is counted before or after that calibration split. Counting pre-split would overstate the events actually available to fit coefficients. Recommend specifying "post calibration-split training minority" in the feature-budget contract.

**N4. [i] Set expectations on timeline.** §32.3 requires ≥300 retained forward trades over ≥12 weeks, gated further by MDE adequacy, with `CONTINUE_EVIDENCE` as a legitimate terminal state. On one symbol/one family this is realistically a multi-month program that may not yield a fast PASS/FAIL — which is the statistically correct design, but worth socializing with the owner so the open-ended horizon is expected rather than read as a stall.

---

## Before locking (ML-00A / ML-01)

The contracts are ready to lock once these two small protocol edits are folded in — both are additive and don't change the architecture:

1. Add the direction-asymmetry diagnostic (and the conditionally-admitted interaction term) to `A3_ML_VALIDATION_PROTOCOL_V1.md`. *(N1)*
2. Specify in the feature-budget rule that `minority_events_min` is the post-calibration-split training minority, and have the data audit emit per-fold budget/purge diagnostics. *(N2, N3)*

Everything else is locked-ready as written.

---

## Bottom line

V1.1 is a materially stronger specification than V1.0 and resolves every issue raised. The statistical-validity backbone — events-based feature budget, causal features with prefix-invariance, fuzzy setup grouping, fold-causal P95-stress slippage labels, paired confidence-bound value gates with an honest underpowered state — is now sound. Proceed to ML-00 inventory and the ML-00A/ML-01 hash-locks; fold in the two protocol notes above as you lock, and carry the direction-symmetry check as the one modeling assumption to actively test once OOS results exist.
