# Review 11 Phase 3 Experimental Reflection and Action Plan

Review source: `C:\Users\ZHAO ZHU INFORMATION\Downloads\PHASE3_EXPERIMENTAL_REVIEW_AND_NEXT_STEPS_2026_05_28.md`

Date reflected: 2026-05-28

## Verdict Accepted

| Area | Decision |
| --- | --- |
| Continue Phase 1 dry-run | GO |
| Continue passive spread logging | GO |
| Continue Phase 2 documentation and preparation | GO |
| Run Phase 3 as a repo-only experimental sandbox | GO, with strict boundaries |
| Use Phase 3 outputs for real readiness gates | NO |
| Authorize Phase 2 paper-mode implementation | NO-GO |
| Authorize broker-side execution | NO-GO |
| Authorize live trading | ABSOLUTE NO-GO |

The Phase 3 lane remains an offline lab. It does not mark Phase 2 as passed, does not modify MT5, and does not enter the owner approval flow for real readiness.

This report has no authority over Phase 2 readiness. PHASE2_READINESS_REPORT.md remains the sole real readiness authority.

## Implementation Response

| Review item | Response |
| --- | --- |
| P3-1: Add Phase 3 CI | Added `.github/workflows/phase3-experimental.yml` to run tests, safety audit, synthetic simulation, status generation, manifest generation, root dashboard generation, and artifact upload. |
| P3-2: Commit fixture | Added `xau-usd/xauusd-phase3-experimental/tests/fixtures/sample_would_signals.csv`. |
| P3-3: Add family de-duplication | Added `family_event_id`, `family_duplicate_group_id`, `family_event_role`, `primary_stream_allowed`, and summary counts for raw observers, unique family events, duplicates, and conflicts. |
| P3-4: Add cost modes | Added `entry_only_proxy`, `entry_exit_proxy`, `p95_fresh_proxy`, and `stress_2x_p95_proxy`; default is `entry_exit_proxy`. |
| P3-5: Add tests | Added fixture-based tests for NORMAL, COST_WATCH, SUSPEND_FAMILY, unsafe row rejection, duplicate handling, conflict handling, safety report generation, and forbidden-reference detection. |
| P3-6: Safety report | Added `PHASE3_EXPERIMENTAL_SAFETY_REPORT.md/json`; latest status is PASS with 0 findings. |
| P3-7: Source manifest | Added `PHASE3_EXPERIMENTAL_MANIFEST.md/json` with source/input/status/script hashes and commit metadata. |
| P3-8: Regenerate dashboard | Regenerated root `status.html` with Phase 3 family de-dup, cost-mode, safety, and manifest fields. |
| P3-9: Authority sentence | Added the exact Phase 2 authority sentence to Phase 3 generated markdown reports and JSON metadata. |
| P3-10: Keep out of owner approval flow | Added explicit status metadata: `owner_approval_flow=excluded_from_real_phase2_phase3_approval_flow`. |

## Latest Experimental Readout

| Metric | Value |
| --- | --- |
| Phase 3 status | `EXPERIMENTAL_COST_SUSPEND_SCENARIO` |
| Raw observer events | 87 |
| Family unique events | 47 |
| Observer duplicates | 40 |
| Observer conflicts | 0 |
| Primary stream allowed | 47 |
| Rejected source rows | 2 |
| Cost mode | `entry_exit_proxy` |
| Median proxy cost | 0.2554R |
| Median net after proxy cost | 0.2562R |
| Kill rule counts | NORMAL 66, COST_WATCH 2, SUSPEND_FAMILY 19 |
| Safety report | PASS |
| Manifest | PASS |

`EXPERIMENTAL_COST_SUSPEND_SCENARIO` means the offline Phase 3 cost proxy found some would-signal rows where projected net expectancy falls below the +0.15R kill threshold. This is useful design pressure, not a real trading gate verdict.

## Remaining Boundaries

| Boundary | Status |
| --- | --- |
| MT5 runtime touched by Phase 3 | False |
| Passive spread logger touched by Phase 3 | False |
| Broker-action code allowed | False |
| Real Phase 2 readiness changed | False |
| Real owner approval advanced | False |

## Next Safe Work

1. Let Phase 1 and spread logging continue uninterrupted.
2. Keep Phase 2 readiness governed only by `PHASE2_READINESS_REPORT.md`.
3. Use Phase 3 reports to design future execution kill rules, not to bypass readiness.
4. If Phase 2 later passes, review the Phase 3 ledger rows with `SUSPEND_FAMILY` before copying any logic into real implementation.
