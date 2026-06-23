# REVIEW — A3 ML V1.2 **Final Pre-Lock Merge Packet**

**Packet under review:** `CODEX_A3_ML_V1_2_FINAL_PRELOCK_MERGE_PACKET_2026_06_21.md`
**Incorporates:** `A3_ML_V1_2_PRELOCK_CLARIFICATIONS_DROPIN_2026_06_21.md` (V1, V2, V3)
**Prior reviews:** spec review, V1.1 review, V1.2 addendum review (all 2026-06-21)
**Review date:** 2026-06-21
**Severity legend:** **[H]** blocker · **[L]** polish · **[i]** informational

---

## Verdict

**GO for hash-lock.** The packet merges all three clarifications faithfully, the contract ownership is coherent, and the manifest is complete. **No open blockers remain on my side.** Proceed: merge → pre-lock verification report → ML-01 hash-lock → ML-00 inventory, A3 paused throughout. The three notes below are optional polish; none should hold up the lock.

The packet also adds genuinely useful operational scaffolding beyond the clarifications: a pre-lock verification report with explicit A3-safety fields (§8), a clean ML-01 capability gate (§9), and a standard hash-lock procedure (§7).

---

## Clarifications merged correctly

**V1 (horizon governance) — merged.** §3 reproduces the clause and correctly targets the execution label contract with the feature-budget cross-reference. The only change is dropping the "per V1.2 §7" pointer, which is right — once the addendum becomes history, contracts shouldn't cite it. Four supporting tests were added (see note 2 below on two of them).

**V2 (interaction admission scope) — merged.** §4 reproduces the clause into the model-selection protocol with the §31 gate values intact (PF ≥1.30 / 5th pct >1.00; expectancy/retained ≥+0.15R / 5th >0; expectancy/raw >0 / 5th >0; incremental delta_R>0 / 5th>0 AND ≥+0.03R or ≥+0.10 PF), and states the +0.01R bar is selection-only. Four executable tests added — all genuinely testable. Good.

**V3 (merge/lock hygiene) — merged and extended.** §5 carries the test-file correction, adds a contract ownership map, and §2 + the §8 manifest policy enforce single-source-of-truth (no clause sourced solely from an un-hashed addendum). This is exactly the intent.

---

## Manifest completeness check

I cross-checked the §7 manifest list against the full V1.1 + V1.2 contract set. **All 16 contracts are present** — the 13 from V1.1 (hypothesis, data, signal-grouping, execution-label, slippage-model, feature-registry.csv, regime, validation, power/MDE, deterministic-benchmark, model-selection, shadow-governance, retraining) plus the 3 from V1.2 (direction-asymmetry, feature-budget, owner-timeline). Nothing was dropped in the merge.

Correctly **excluded** from the contract manifest: data audits and reports (they are outputs, not contracts), the fitted slippage JSON (data-derived, hashed later at model-registry time per §40), and the addendum/review files (revision history). This is the right boundary.

---

## Minor notes (none blocking)

**1. [L] The §5 ownership map is partial, and "slippage labels" is ambiguously assigned.** The map covers the 7 merge-touched contracts, which is fine for its purpose — but it's titled "Final contract ownership map," which reads as complete, and it assigns "slippage labels" to the execution label contract while a dedicated `A3_ML_SLIPPAGE_MODEL_CONTRACT_V1.md` exists (and is in the manifest). Recommend either labeling the map "merge-touched contracts only" or completing it for all 16, and disambiguating slippage: the slippage **model/distributions** stay owned by the slippage-model contract; the execution label contract **references** it for label application rather than re-owning it. This avoids the exact duplicate-wording conflict the §6 checklist is trying to prevent.

**2. [L] Two of the four V1 horizon "tests" are process gates, not unit tests.** `test_horizon_sensitivity_is_mechanics_only` and `test_horizon_sensitivity_contains_no_outcome_metrics` are genuinely assertable against the sensitivity-table schema. But `test_horizon_change_cannot_reference_feature_budget` and `test_horizon_change_requires_new_contract_version` are governance/review controls that can't be meaningfully asserted in pytest and risk becoming always-pass stubs — which is worse than no test, because it implies coverage that doesn't exist. Implement those two as CI/manifest/version assertions or move them to the review checklist; keep the two schema tests as unit tests.

**3. [i] Confirm no legacy A3 open position before verification.** §8 sets `A3_open_positions = 0` and `A3_pending_orders = 0` as passing values — a good belt-and-suspenders safety gate. Since the ML work is repo-only/shadow-only it won't create positions, but confirm there's no pre-existing position on the paused lanes that would (correctly) fail the check, so verification doesn't surprise anyone.

---

## Bottom line

The four-round review is closed. Every finding from the original spec review through the V1.2 addendum has been resolved, and this packet operationalizes the merge cleanly — faithful clause text, a complete manifest, single-source-of-truth enforcement, and a safety-checked verification gate before ML-01. **Approved to hash-lock.** Fold in notes 1 and 2 during the merge if convenient; confirm note 3 as part of the verification report. A3 stays paused, no model is trained before ML-01, and the program's honest terminal states (including `CONTINUE_EVIDENCE`) remain intact.
