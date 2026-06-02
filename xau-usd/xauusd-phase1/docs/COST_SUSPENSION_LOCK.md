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

## Boundary

Canonical Phase 2 paper-mode implementation, broker-side execution, demo trading as Phase 2 evidence, and live/real-capital use remain NO-GO while this lock is active.
