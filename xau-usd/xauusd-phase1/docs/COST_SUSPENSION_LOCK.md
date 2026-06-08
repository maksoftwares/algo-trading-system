# Cost Suspension Lock

family: `breakout_retest_family`
status: `COST_SUSPENDED_CANONICAL`
effective_date: `2026-06-02`

## Reason

Measured-cost revalidation failed and the measured-cost sanity check confirmed the calculation path. The failure is therefore treated as real unless a future reproducible cost-conversion bug is proven.

## Applies To

- `breakout_retest`
- `swing_breakout_retest_v0`
- `symbol_normalized_round_retest_v0`
- `quarter_round_retest_v0`
- `session_extreme_retest_v0`
- `round_number_retest_v0`
- all future same-family level/retest variants

## Cannot Be Reactivated By

- owner override alone
- demo fills
- same-family variant pass
- lower-spread subset
- strategy filter added to v1.0

## Reactivation Requires

- new versioned hypothesis or corrected cost bug
- fresh Phase 0/0R evidence
- measured-cost revalidation PASS
- owner approval

## 2026-06-08 Actual Demo Cost Note

`PHASE2_ACTUAL_DEMO_COST_RECONCILIATION.md` is PASS and marks the current actual-demo cost concern as resolved for the wider-stop demo/weakness-review lane. Current direct-MT5 broker-inclusive demo trades are positive after duplicate hiding, and `P2WEAKNESS_BR_V1` observed estimated cost_R below the +0.15R floor.

This does not reactivate the old tight-stop canonical v1.0 ledger. It means the practical demo question has shifted from "is cost fatal?" to "does the edge quality, win rate, session behavior, duplicate exposure, and sample size justify a new locked cost-aware hypothesis?"

## Boundary

Canonical Phase 2 paper-mode implementation, broker-side execution, demo trading as Phase 2 evidence, and live/real-capital use remain NO-GO while this lock is active.
