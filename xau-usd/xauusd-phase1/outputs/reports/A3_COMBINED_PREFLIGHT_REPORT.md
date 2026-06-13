# A3 Combined Preflight Report

Status: **PENDING**

## Boundary

- A3 login: `1033669`.
- Demo only; canonical Phase 2 unchanged.
- A2 remains untouched.
- Committed defaults remain non-executing.

## Checks

| Check | Status | Evidence |
|---|---|---|
| t4_equivalent_source_tests_both_eas | PASS | ============================= 22 passed in 0.12s ============================== |
| mandatory_source_safety_both_eas | PASS | source/preset checks |
| hypotheses_hash_locked_both_eas | PASS | LOCKED_BEFORE_FIRST_TRADE |
| decommission_pass | PASS | WR50/P2WEAKNESS decommission gate. |
| dry_run_session_both_eas_pass | PENDING | Both EAs require dry-run logs before arming. |
| owner_signature_and_local_preset | PENDING | Owner must sign and supply local execution preset. |

## Attach Decision

- Decision: `DO_NOT_ATTACH`
- Monday attach gate: `CLOSED_UNTIL_ALL_CHECKS_PASS`
- Target account: `1033669`
