# Cost Suspension Policy

Status: ACTIVE

A candidate family enters `COST_SUSPENDED_CANONICAL` when measured-cost revalidation fails after the measured-cost model is PASS and no forensic bug is confirmed.

## Effects

| Permission | Value while suspended |
| --- | --- |
| Canonical Phase 2 paper-mode execution | false |
| Demo execution as Phase 2 evidence | false |
| Live execution | false |
| Same-family diversification claim | false |
| Phase 0R replacement research | true |

## Current Suspended Family

The breakout-retest family is `COST_SUSPENDED_CANONICAL`:

```text
breakout_retest
swing_breakout_retest_v0
symbol_normalized_round_retest_v0
quarter_round_retest_v0
round_number_retest_v0
session_extreme_retest_v0
future same-family level/retest variants
```

No same-family variant can become execution-eligible unless a future measured-cost-aware process explicitly reopens the family.
