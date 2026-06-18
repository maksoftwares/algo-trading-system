# Phase1 Test Failure Triage - 2026-06-18

Status: `REVIEW_REQUIRED`

Command:

```text
cd xau-usd/xauusd-phase1
..\xauusd-phase0\.venv\Scripts\python.exe -m pytest tests -q
```

Captured output:

```text
xau-usd/xauusd-phase1/outputs/reports/PHASE1_PYTEST_D5DD2DE_2026_06_18.txt
```

Post A3-emergency-pause captured output:

```text
xau-usd/xauusd-phase1/outputs/reports/PHASE1_PYTEST_A3_PAUSE_2026_06_18.txt
```

Result:

```text
399 passed, 6 failed
```

The post-pause run has the same result:

```text
399 passed, 6 failed
```

## Failure Triage

| Test | Failure summary | Classification | Required fix |
| --- | --- | --- | --- |
| `tests/test_phase1_acceptance_report.py::test_acceptance_report_is_pending_until_soak_duration_is_complete` | Expected `PENDING`; generated acceptance status is now `FAIL`. | `STALE_TEST_EXPECTATION_OR_ACCEPTANCE_RULE` | Reconcile Phase1 acceptance semantics after broker-action/demo-management artifacts; update either generator or test expectation with explicit governance boundary. |
| `tests/test_phase1_acceptance_report.py::test_acceptance_report_warns_when_runtime_is_stale` | Expected `PENDING`; generated acceptance status is now `FAIL`. | `STALE_TEST_EXPECTATION_OR_ACCEPTANCE_RULE` | Same as above; stale runtime should remain non-PASS, but the test must reflect the current acceptance-status taxonomy. |
| `tests/test_phase1_static.py::test_phase1_safety_audit_has_no_findings` | Safety audit now finds 14 broker-action terms, including `OrderSend` in `Account3ProfitLockExitManager.mq5`. | `EXPECTED_GOVERNANCE_UPDATE` | Scope safety audit by domain: passive/dry-run files remain strict; owner-authorized demo executors and SLTP-only managers require explicit allowlist and action-type checks. |
| `tests/test_phase1_status_summary.py::test_status_summary_writes_machine_readable_snapshot` | Expected acceptance `PENDING`; generated status summary reports acceptance `FAIL`. | `STALE_TEST_EXPECTATION_OR_ACCEPTANCE_RULE` | Update status-summary test after acceptance semantics are reconciled. |
| `tests/test_phase2_experimental_demo_executor.py::test_demo_executor_is_demo_scoped_and_explicitly_armed` | Test expects `InpEURUSDFixedLot = 0.05`; source no longer contains that literal. | `REAL_CODE_OR_TEST_CONTRACT_DRIFT` | Decide whether EURUSD fixed-lot input is still required. If yes, restore source contract; if no, update the test and governance docs. |
| `tests/test_phase2_transition_artifacts.py::test_phase2_transition_artifact_verifier_passes_committed_artifacts` | `PHASE2_DEMO_PREFLIGHT.json` is stale relative to canonical inputs. | `STALE_ARTIFACT` | Regenerate and commit `PHASE2_DEMO_PREFLIGHT.json` and matching report after safety-audit taxonomy is updated. |

## Owner Decision

Do not treat this suite as clean. The broker-action/SLTP manager additions are not automatically unsafe, but the old Phase1 static checks are too broad for the current repository. The next code fix should be test-taxonomy work, not another runtime trading change.

## Boundary

This triage artifact is documentation only. It makes no MT5 runtime, EA, chart, preset, order, or position changes.
