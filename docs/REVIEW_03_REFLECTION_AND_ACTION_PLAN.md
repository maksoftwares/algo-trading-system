# Review 03 Reflection and Action Plan

Date: 2026-05-22

Review #3 is accepted as directionally correct. The project has better process evidence than before, but the edge claim is now narrower: one breakout-retest edge family, expressed in two timeframe variants, with high cost sensitivity. Phase 2 remains justified only as a paper-mode cost-measurement experiment, not as a profit-confirmation phase.

## Immediate Findings

| ID | Reviewer concern | Current answer | Status | Evidence |
| --- | --- | --- | --- | --- |
| V1 | Is 0.3228R mean cost measured or assumed? | It is modeled/provisional from the fixed-notional report, not yet accepted as a measured 4-week cost model. The passive spread logger is running, but measured-cost revalidation remains pending. | PENDING | `xau-usd/xauusd-phase0/outputs/reports/FIXED_NOTIONAL_REPORT.md`, `xau-usd/xauusd-phase0/outputs/reports/MEASURED_COST_MODEL.md`, `xau-usd/xauusd-phase0/outputs/reports/BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md` |
| V2 | Re-run D2 against the full candidate universe. | Re-run completed again after `m5_impulse_continuation_v0`. `breakout_retest` remains winner across 22 non-empty matrix-ledger candidates. White p=0.0200, max pairwise SPA p=0.0264. | PASS | `xau-usd/xauusd-phase0/outputs/reports/PHASE0_REALITY_CHECK.md` |
| V3 | Aggregate rejected-candidate gate reasons to test frequency bias. | Audit generated after `m5_impulse_continuation_v0`. 21 rejected/research candidates were audited. 4 had sample-size failures, all 21 had multi-cell expectancy failures, and 0 were frequency-only failures. | PASS | `xau-usd/xauusd-phase0/outputs/reports/PHASE0_REJECTED_CANDIDATE_GATE_AUDIT.md` |
| V4 | Confirm cost-sensitivity used P95 costs. | The 9-cell matrix includes best/median/P95 cost cells and the fixed-notional report exposes P95 cells separately. Phase 2 still requires measured P95 replacement before authorization. | PENDING_MEASURED_COST | `xau-usd/xauusd-phase0/outputs/reports/FIXED_NOTIONAL_REPORT.md` |
| V5 | Treat `swing_breakout_retest_v0` as same-family, not diversification. | Accepted. It remains useful telemetry, but capital and risk docs must treat v1 as single-edge. | PASS | `xau-usd/xauusd-phase1/docs/PHASE2_AUTHORIZATION_CHECKLIST.md` |
| V6 | Complete the five-day soak. | Still wall-clock dependent. Acceptance remains pending until the soak report closes. | PENDING | `xau-usd/xauusd-phase1/outputs/reports/PHASE1_ACCEPTANCE_REPORT.md` |

## D2 Full-Universe Rerun

Command:

```powershell
.\.venv\Scripts\phase0.exe run-reality-check --approved-expert breakout_retest --iterations 5000 --block-months 3 --max-pvalue 0.10
```

Result:

| Metric | Value |
| --- | ---: |
| Status | PASS |
| Winner | breakout_retest |
| Non-empty matrix-ledger candidates | 22 |
| White Reality Check p-value | 0.0200 |
| Max pairwise SPA p-value | 0.0264 |
| Bootstrap iterations | 5000 |
| Block length | 3 months |

Interpretation: the stale-N concern is closed for the currently available matrix universe. This does not make the edge risk-free; it only means the D2 p-value has now been recomputed against the full tested non-empty ledger set.

## Frequency-Bias Audit

Command:

```powershell
.\.venv\Scripts\phase0.exe generate-rejection-gate-audit
```

Result:

| Metric | Value |
| --- | ---: |
| Audited candidates | 23 |
| Approved/same-family candidates excluded from rejection counts | 2 |
| Rejected/research candidates audited | 21 |
| Sample-size failures | 4 |
| Multi-cell expectancy failures | 21 |
| Both expectancy and sample-size failures | 4 |
| Frequency-only failures | 0 |

Interpretation: the current evidence does not show candidates being rejected only because they were low-frequency. Frequency pressure exists for some candidates, but every rejected/research candidate also failed multi-cell expectancy survival. `m5_impulse_continuation_v0` was rejected on expectancy despite high trade count.

## Phase 2 Framing

Phase 2 should proceed only when the existing authorization checklist closes, and it should be framed as:

```text
Paper-mode cost-measurement experiment.
Single-edge breakout-retest family.
No live capital.
No victory-lap assumption.
```

Pre-commitment to add before authorization:

```text
If measured live/paper execution cost pushes breakout_retest net expectancy below +0.10R, suspend the expert family and return to research.
```

## Remaining Blockers

| Blocker | Why it remains open |
| --- | --- |
| Measured cost model | Current measured report is PENDING: 6390 rows across 2 observed days, with 5 observed days required. |
| Measured-cost revalidation | Cannot run to PASS until measured cost model is PASS. |
| Five-day Phase 1 soak | Wall-clock evidence has not elapsed yet. |
| Owner Phase 2 approval | Must be explicit after cost and soak gates close. |
| Independent diversification | `swing_breakout_retest_v0` is same-family; continue searching for a non-breakout-retest candidate, but do not tune rejected v0s. |

## Next Actions

1. Let the Phase 1 soak and passive spread logger continue.
2. Keep regenerating measured-cost reports from `C:\MT5PortableSpreadLogger\MQL5\Files`.
3. Use `xau-usd/xauusd-phase1/docs/PHASE2_OWNER_APPROVAL_TEMPLATE.md` only after objective readiness gates pass; do not create the live approval file early.
4. Continue independent candidate research only with new, locked hypotheses and the no-tuning rule.
