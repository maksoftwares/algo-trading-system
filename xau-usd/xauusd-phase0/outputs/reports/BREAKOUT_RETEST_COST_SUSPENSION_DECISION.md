# Breakout-Retest Cost Suspension Decision

Overall status: COST_SUSPENDED_CANONICAL

Decision date: 2026-06-02

## Decision

The breakout-retest family is suspended for canonical Phase 2 execution.

| Evidence | Status | Result |
| --- | --- | --- |
| Measured cost model | PASS | 71,577 fresh rows across 5 fresh observed market days. |
| Measured-cost revalidation | FAIL | 0/9 passing cells under measured P95 cost. |
| Measured-cost assumption delta | FAIL | Measured P95 spread is 75 points vs configured P95 35 points. |
| Sanity check | CALCULATION_CONFIRMED | No unit, point-size, spread-counting, or denominator bug found. |

## Affected Family

This family-level suspension applies to:

```text
breakout_retest
swing_breakout_retest_v0
symbol_normalized_round_retest_v0
quarter_round_retest_v0
session_extreme_retest_v0
round_number_retest_v0
all future same-family level/retest variants
```

## Boundary

This decision does not invalidate historical Phase 0 evidence. It says that the family is not execution-eligible under the current measured XAUUSD cost environment.

Canonical Phase 2 paper-mode implementation, broker-side execution, demo trading as Phase 2 evidence, and live trading remain blocked.
