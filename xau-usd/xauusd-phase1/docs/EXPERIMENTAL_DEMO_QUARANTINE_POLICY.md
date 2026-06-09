# Experimental Demo Quarantine Policy

Status: ACTIVE

`Phase2ExperimentalDemoExecutor.mq5` is quarantined, owner-requested, non-canonical demo code. It is not Phase 2 paper-mode implementation and cannot provide Phase 2 readiness evidence.

## Required Labels

Any experimental order log must carry:

```text
experimental_quarantine=true
canonical_phase2_evidence=false
phase2_readiness_override=false
candidate_family_status=COST_SUSPENDED_CANONICAL
```

## Required Guards

- Demo server only.
- Account login whitelist.
- Explicit experimental authorization token.
- Explicit cost-suspension acknowledgement token.
- Candidate allowlist.
- Account daily order cap.
- No account-level open exposure cap; exposure count remains logged for review.
- Kill switch file.
- Cost_R pre-order guard.
- Spread pre-order guard.
- Fixed lot default <= 0.01.
- Separate experimental magic namespace.

## Non-Authority

Experimental demo fills, logs, win rate, or PnL cannot override `PHASE2_READINESS_REPORT.md`, `BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md`, `MEASURED_COST_ASSUMPTION_DELTA.md`, or `BREAKOUT_RETEST_COST_SUSPENSION_DECISION.md`.
