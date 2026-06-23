# INDEPENDENT REVIEW — A3 ML C00 Final Contract Merge

**Repository:** `maksoftwares/algo-trading-system`
**Scope:** A3 Python ML Signal-Quality Program V1.2 — C00 contract merge only
**Account / symbol / family:** A3 `1033669` · XAUUSD · breakout_retest · repo-only / shadow-only
**Reviewed against:** master implementation plan V1.2 FINAL, V1.2 final pre-lock merge packet, V1.2 pre-lock addendum, V1.1 spec
**Review date:** 2026-06-21
**Evidence:** read all 16 contracts + registry + commit report + 6 tests; ran the suite (24 passed); ran a mutation test (clause removal/reorder → test fails); inspected git state and the runtime-auth evidence JSON.

---

## VERDICT

```
PASS_WITH_CONDITIONS_C00_GO_C01_AFTER_FIXES
```

The substance of C00 is correct, complete, internally consistent, and safe. All 16 owning contracts exist, every approved V1.2 clarification is merged into its owning contract (nothing left only in an addendum), the contracts keep A3 paused and shadow-only, no training/broker/runtime code was added, and the tests are meaningful (proven to fail when a clause is removed). No FAIL-level defect exists. Two items must be handled before the C01 SHA256 lock — commit hygiene and consistent cross-contract duplication — and C01 must complete the live A3 exposure query that C00 could not.

---

## Findings by severity

### No blockers
Nothing found rises to FAIL. The merge is faithful and the safety boundary is intact.

### MEDIUM

**M1 — C00 is not actually committed, and the working tree is dirty with unrelated changes (lock-contamination risk).**
All 16 contracts, the registry, the 6 tests, and the report are **untracked** (`git status` → `??`), yet `docs/A3_ML_COMMIT_1_CONTRACT_MERGE_REPORT.md:3` declares `Status: CONTRACTS_CREATED_TARGETED_TESTS_PASS` and the file is titled "Commit 1." Separately, the tree carries unrelated modified files — `xau-usd/xauusd-phase1/docs/A1_XAU_920101_EVENING_CORE_FORWARD_V0_SPEC_2026_06_20.md` (+ its `.sha256.json`), `outputs/reports/RUNTIME_AUTHORIZATION_RECONCILIATION_2026_06_19.{json,md}`, `outputs/reports/A3_NET_COST_DEDUPED_REBASELINE_TRADES_2026_06_19.csv`, `RUNTIME_CHART_INVENTORY_FORENSIC_2026_06_21.csv`, `status_summary.json`, and a phase0r hypothesis. Risk: a non-surgical `git add -A` at C01 would fold unrelated runtime/authorization changes into the contract-lock commit and contaminate the SHA256 manifest.
*Required fix:* commit the C00 set as its own surgical commit (explicit paths for the 16 contracts + registry + 6 tests + report + the runtime-auth evidence JSON), excluding all unrelated modified files; reconcile the report wording so "Commit 1 / CONTRACTS_CREATED" matches the actual committed state.

**M2 — Consistent duplication of locked clauses across contracts (single-source-of-truth).**
Two clauses are stated in two contracts each. They currently agree, so there is no contradiction, but locking duplicated prose invites future drift:
- Per-fold diagnostic schema appears in both `A3_ML_DATA_CONTRACT_V1.md:105–130` and `A3_ML_FEATURE_BUDGET_CONTRACT_V1.md:73–100`.
- The P50/P95 slippage application rule ("expected = adverse P50, stress = adverse P95, no favorable TP slippage") appears in both `A3_ML_EXECUTION_LABEL_CONTRACT_V1.md:84–92` and `A3_ML_SLIPPAGE_MODEL_CONTRACT_V1.md:53–59`.
*Required fix:* before the lock, consolidate each to a single owner with a cross-reference (per-fold schema → feature-budget owns, data-contract references; slippage numeric application → slippage-model owns, execution-label references). The C01 "duplicate-clause/conflict scan" must treat consistent duplication as in-scope, not only literal conflicts.

### LOW / INFORMATIONAL

**L1 — Drift-threshold detail is not in any locked contract.** The locked set carries only the drift *response* (`A3_ML_SHADOW_GOVERNANCE_V1.md:54–62`, `ML_SHADOW_DISABLED`; ABSTAIN on drift lock in model-selection). The detailed drift metrics/thresholds (score PSI, base-rate/Brier/calibration/retention/PF drift) live only in the un-hashed master plan (§36). Acceptable for C00 — the drift module is a later commit — but ensure those thresholds land in a hashed contract when `drift.py` is built so they are not lost from the locked governance set.

**L2 — Runtime-auth evidence is a profile reconciliation, not a live broker query (correctly disclosed).** `outputs/reports/A3_ML_PREIMPLEMENT_RUNTIME_AUTH_CHECK.json` is read-only (`boundary.orders_sent=False`, `positions_closed=False`, status `PASS_CURRENT_PRIOR_DRIFT_REMEDIATED`). The report is explicitly honest that the live MetaTrader5 position/order query could not run (no package) and defers it to C01 fail-closed (`A3_ML_COMMIT_1_CONTRACT_MERGE_REPORT.md:26`), matching master-plan line 65. Not a defect; restated here as a hard C01 gate.

---

## Answers to the 16 review questions

1. **All 16 owning contracts present?** Yes — all 16 + `A3_ML_FEATURE_REGISTRY_V1.csv`, each `Status: PRELOCK_CONTRACT`.
2. **Any approved clause only in an addendum/review?** No — horizon governance is in execution-label (122–142), interaction-scope/gate-preservation in model-selection (54–62), slippage split across execution-label + slippage-model. Verified by `test_a3_ml_contracts.py` ownership tokens.
3. **Contradictions between contracts?** None. Two consistent duplications only (see M2).
4. **Slippage ownership cleanly split?** Yes — slippage-model owns fitting/distributions/adequacy/fold-causal leakage control; execution-label references it and defines P50/P95 application (`A3_ML_EXECUTION_LABEL_CONTRACT_V1.md:7,84–92`).
5. **Horizon governance merged, incl. "cannot change to enlarge budget"?** Yes — `A3_ML_EXECUTION_LABEL_CONTRACT_V1.md:122–142` + cross-ref in feature-budget (113–115).
6. **Feature budget post-purge/embargo/unresolved/calibration?** Yes — explicit 8-step ordering, `A3_ML_FEATURE_BUDGET_CONTRACT_V1.md:19–40`.
7. **Budget = global minimum across outer folds?** Yes — `minority_events_min = minimum ... across all outer folds`, `min(16, floor(minority_events_min/15))` (35–37).
8. **Forbids separate L/S models, only one interaction?** Yes — `A3_ML_DIRECTION_ASYMMETRY_PROTOCOL_V1.md:11,84–97`.
9. **Interaction consumes budget, replaces only last prefix feature?** Yes — direction-asymmetry (93–95) + feature-budget (63–71).
10. **Interaction admission preserves all final P95-stress gates?** Yes — `A3_ML_MODEL_SELECTION_PROTOCOL_V1.md:54–62` and 124–158; "does not lower, waive, or substitute for any final candidate gate."
11. **Horizon-sensitivity mechanics-only, no PF/expectancy/win-rate/threshold/score?** Yes — `A3_ML_DATA_CONTRACT_V1.md:132–156`; enforced by `test_a3_ml_horizon_sensitivity.py`.
12. **A3 lanes paused, profit-lock dry-run/disarmed?** Yes — `A3_ML_SHADOW_GOVERNANCE_V1.md:7–15`, meta-hypothesis 64–72.
13. **No MT5 runtime change / armed preset / broker code / training / threshold / data mining?** Yes — C00 added only docs + tests; no `ml/a3_meta_v1/` module, scripts, `.mq5/.mqh`, or order code. The only `OrderSend/CTrade` strings are in the safety test asserting they are prohibited.
14. **Tests meaningful, not always-pass stubs?** Yes — 24 passed; mutation test confirmed failures when `DRY_RUN_DISARMED` was removed and when the calibration step was reordered.
15. **Report honest about MetaTrader5 unavailable / not proving live position state?** Yes — `A3_ML_COMMIT_1_CONTRACT_MERGE_REPORT.md:26`; defers to C01 fail-closed.
16. **Safe to proceed to C01?** Yes, after the M1/M2 fixes; C01 must complete the live A3 zero-exposure + open-position/order query and fail closed if MT5 is unavailable.

---

## Required fixes before the C01 SHA256 lock

1. Surgically commit the C00 contract set (and the runtime-auth evidence), excluding the unrelated dirty files; align the "Commit 1" report with the real commit. *(M1)*
2. Consolidate the two duplicated clauses to single owners with cross-references. *(M2)*
3. Carry into C01 as hard gates (already mandated, restate): live A3 zero-exposure + open-position/order query with fail-closed on MT5 unavailability; duplicate-clause/conflict scan covering consistent duplication.

No model training, threshold selection, broker action, runtime change, or arming is approved by this review.

---

## Go / No-Go — C01 only

**GO for C01 (pre-lock verification + manifest), conditional on the two pre-lock fixes above.** C00's contracts are sound and safe; do not perform the SHA256 hash-lock until M1 and M2 are resolved and the C01 live A3 exposure query passes or fails closed. No authorization beyond C01 is granted.
