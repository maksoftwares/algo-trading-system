# Phase 1 Gap Classification Review

Overall status: SHARED_CLASSIFIER_ACTIVE

Last updated: 2026-05-27

## Reviewed Gap

| Field | Value |
| --- | --- |
| Left bar | 2026.05.26 20:55:00 |
| Right bar | 2026.05.26 22:00:00 |
| Duration | 65 minutes |
| Prior interpretation | Runtime WARN / active-market reset |
| Current interpretation | Expected broker maintenance pause under configured break policy |
| Classifier source | `xau-usd/xauusd-phase1/scripts/phase1_gap_classifier.py` |
| Config source | `xau-usd/xauusd-phase1/PHASE1_EXPECTED_MARKET_BREAKS.yaml` |

## Policy Update

Review V4 accepted Option A:

```text
Expected broker maintenance breaks pause the active-market streak but do not reset it.
Closed-market time inside those breaks does not count toward the 72h active-market total.
Unexpected gaps, run resets, stale/closed unsafe rows, dry-run violations, permission violations,
and server-time violations still reset or warn.
```

This is a reporting/gate-stability change only. It does not change MT5 runtime behavior, trading permissions, observer thresholds, costs, or any broker execution boundary.

## Shared Classifier Coverage

| Consumer | Uses shared classifier |
| --- | --- |
| `phase1_soak_streak.py` | Yes |
| `verify_phase1_logs.py` | Yes |
| `analyze_phase1_soak.py` | Yes |
| `generate_phase1_runtime_health_report.py` | Yes |
| `generate_phase1_status_summary.py` | Indirectly through soak/health reports |
| `generate_phase1_acceptance_report.py` | Indirectly through status summary / soak streak |
| `generate_phase2_readiness_report.py` | Indirectly through Phase 1 acceptance/status inputs |

## Classification Rules

| Gap type | Active-market streak | Runtime warning |
| --- | --- | --- |
| Normal M5 cadence / tolerated small gap | Continues | No |
| Configured daily broker maintenance break | Pauses, with elapsed closed-market time excluded | No |
| Weekend market break | Pauses, with elapsed closed-market time excluded | No |
| Expected rollover market break | Pauses when classified as expected | No |
| Unexpected active-market gap | Resets | Yes |
| `run_id` change / restart | Resets | Lifecycle/readiness gate |
| Unsafe state row | Resets or fails | Yes |

## Phase 2 Effect

Phase 2 remains NO-GO. The shared classifier prevents expected broker maintenance from making the 72h active-market gate impossible, but it does not close the gate by itself. Phase 2 still requires:

| Gate | Status |
| --- | --- |
| Active-market 72h streak | PENDING |
| Process/code-freeze 96h | PENDING |
| Measured cost model | PENDING |
| Measured-cost revalidation | PENDING |
| Observer parity | PENDING |
| VPS latency evidence | PENDING |
| Owner approval | PENDING |
