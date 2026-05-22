# Review Response - 2026-05-21

This file maps the external review findings to concrete repository actions.

## Accepted Findings

| Finding | Response |
| --- | --- |
| Complete the five-day Phase 1 soak honestly. | Accepted. Phase 1 acceptance remains `PENDING` until the wall-clock soak is complete. |
| Start a second candidate expert in research mode. | Accepted. `SECOND_CANDIDATE_RESEARCH_PLAN.md` starts the `squeeze_breakout_long_v0` track without registering or testing it yet. |
| Add D1 / D2 before live pilot. | Accepted and implemented. `PHASE0_INDEPENDENT_VALIDATION.md` records CPCV and Reality Check/SPA as PASS for `breakout_retest`. |
| Verify D3 / D4 explicitly. | Accepted and implemented. `PHASE0_INDEPENDENT_VALIDATION.md` records both D3 and D4 as closed for the current evidence package. |
| Audit the breakout-retest edge thesis. | Accepted. The current hypothesis already contains the edge mechanism, failure modes, code mapping, and falsification criteria; a separate edge-thesis file may still be added if reviewers want a standalone artifact. |
| Add Phase 1 CI visibility. | Accepted and implemented. `.github/workflows/phase1.yml` runs Phase 1 tests, dry-run safety audit, and uploads committed review reports. |
| Document workspace ownership. | Accepted. The active Windows paths are machine-local, not canonical project assumptions. |
| Reduce report overhead later. | Accepted. Canonical reporting policy should keep one machine-readable summary, one acceptance report, and one review bundle as the primary review surfaces. |

## Local Verification Mapping

| Reviewer check | Local artifact |
| --- | --- |
| Gate 1 matrix survival | `outputs/reports/phase0_breakout_retest_results.md` |
| Concentration gates | `outputs/reports/phase0_breakout_retest_results.md` |
| Decile gate | `outputs/reports/phase0_breakout_retest_results.md` |
| Cost sensitivity | `outputs/reports/phase0_breakout_retest_results.md` |
| Multi-symbol check | `outputs/reports/phase0_breakout_retest_results.md` |
| Gate 9 adversarial review | `outputs/adversarial_review/breakout_retest_adversarial_score.md` |
| Intrabar ambiguity | `outputs/reports/breakout_retest_intrabar_ambiguity_report.md` |
| Final verdict | `outputs/reports/PHASE0_VERDICT.md` |
| Real artifact verification | `outputs/reports/PHASE0_REAL_ARTIFACT_VERIFICATION.md` |
| D1 CPCV validation | `outputs/reports/PHASE0_CPCV_VALIDATION.md` |
| D2 Reality Check / SPA-style bootstrap | `outputs/reports/PHASE0_REALITY_CHECK.md` |
| D3 / D4 independent validation status | `docs/PHASE0_INDEPENDENT_VALIDATION.md` |
| Cost reporting policy | `docs/COST_REPORTING_POLICY.md` |
| Fixed-notional cost report | `outputs/reports/FIXED_NOTIONAL_REPORT.md` |

## Decision

Current project decision remains:

```text
Phase 0 closed for breakout_retest: YES
Phase 1 dry-run shell: YES
Phase 2 paper trading: NOT YET
Live deployment: NO
```

The next highest-leverage work is to keep Phase 1 soaking and pre-register a second candidate research track without changing the approved `breakout_retest` package.
