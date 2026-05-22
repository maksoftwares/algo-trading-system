# Phase 1 Review Index

Overall status: FAIL

## Current Decision

One or more review artifacts are missing or failing. Keep the shell dry-run and resolve the failed evidence.

## Latest Runtime Snapshot

| Decision Rows | Latest Bar | Dry Run | Permission | Server Time | BR Stage |
| --- | --- | --- | --- | --- | --- |
| 4 | 2026.05.22 11:10:00 | true | false | CLOCK_OK | WAIT_LEVEL_BREAK_RETEST |

## Gate Snapshot

| Log | Soak | Runtime | Would-Signal | Acceptance | Soak Progress | Would Rows | Clusters |
| --- | --- | --- | --- | --- | --- | --- | --- |
| WARN | PASS | WARN | WARN | PENDING | 0.14% | 0 | 0 |

## Primary Artifacts

| Artifact | Status | Path | Note |
| --- | --- | --- | --- |
| Acceptance report | PENDING | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_ACCEPTANCE_REPORT.md | Overall status: PENDING. |
| Runtime health report | WARN | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_RUNTIME_HEALTH_REPORT.md | Overall status: WARN. |
| Runtime log report | WARN | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_DRY_RUN_LOG_REPORT.md | Overall status: WARN. |
| Soak/drift report | PASS | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_DRIFT_REPORT.md | Overall status: PASS. |
| Would-signal report | WARN | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_WOULD_SIGNAL_REPORT.md | Overall status: WARN. |
| Soak history report | WARN | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY_REPORT.md | Overall status: WARN. |
| Phase 2 readiness report | FAIL | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_READINESS_REPORT.md | Overall status: FAIL. |
| Status summary JSON | PASS | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_STATUS_SUMMARY.json | Present; 2257 bytes. |
| Would-signal review CSV | PASS | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_WOULD_SIGNAL_REVIEW.csv | Present; 276 bytes. |
| Soak history CSV | PASS | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY.csv | Present; 46302 bytes. |

## Historical Note

Historical acceptance FAIL rows were seen from 2026-05-21T22:12:57.446733+00:00 to 2026-05-22T11:08:17.659899+00:00; some were acceptance-only while all underlying runtime checks were PASS, so treat them as reporting transients.

## Review Bundle

- Bundle: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\review_bundles\PHASE1_DRY_RUN_BUNDLE_20260522_064156.zip`
- Manifest: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\review_bundles\PHASE1_DRY_RUN_BUNDLE_20260522_064156_manifest.json`

## Boundary

- Current work remains dry-run only.
- Broker-action code remains outside the approved scope.
- Final Phase 1 acceptance still depends on the five-trading-day soak gate.
