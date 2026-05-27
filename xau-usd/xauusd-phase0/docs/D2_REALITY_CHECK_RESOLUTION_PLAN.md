# D2 Reality Check Resolution Plan

Last updated: 2026-05-27

## Current Status

Status: FAIL

The canonical fixed-notional monthly R-series Reality Check / SPA rerun now uses the full non-empty matrix-ledger universe. `breakout_retest` remains the winner and White's Reality Check p-value remains strong, but the expanded universe triggers the stricter `0.01` effective alpha rule.

| Metric | Value |
| --- | ---: |
| Non-empty candidates | 66 |
| Winner | `breakout_retest` |
| White Reality Check p-value | 0.0002 |
| Max pairwise SPA p-value | 0.0174 |
| Effective alpha | 0.01 |
| Status | FAIL |

## Why It Failed

The failing pairwise checks are against same-family alternatives:

| Alternative | Interpretation |
| --- | --- |
| `round_number_retest_v0` | Same breakout-retest family; round-number level variant. |
| `symbol_normalized_round_retest_v0` | Same breakout-retest family; symbol-normalized round-number variant. |

This does not make those alternatives true diversification. It means the evidence is not yet clean enough to say `breakout_retest` is statistically dominant over all same-family variants at the stricter expanded-universe threshold.

## Boundary

- Phase 1 dry-run telemetry may continue.
- Passive spread logging may continue.
- Independent candidate research may continue.
- Phase 2 paper-mode broker execution remains blocked.
- Live execution remains blocked.

## Resolution Options

1. Keep D2 as-is and require a PASS before Phase 2. This is the strictest option and currently blocks Phase 2.
2. Pre-register a family-clustered D2 method, then rerun it as a separate exploratory-to-canonical review decision. This must not be used retroactively without reviewer approval.
3. Continue independent-family candidate research until a genuinely different edge survives first-pass gates, then rerun D2 with clearer family separation.
4. Proceed only with dry-run and cost measurement evidence while marking Phase 2 paper execution as not authorized.

## Next Action

Do not tune `breakout_retest` or the same-family alternatives to force D2. Continue the independent EA search and keep the Phase 1 dry-run / measured-cost soak running until the objective wall-clock gates mature.
