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

The method decision is now recorded in `D2_METHOD_DECISION_2026_05_27.md`.

1. Keep the current fixed-notional candidate-level D2 as the canonical Phase 2 readiness gate.
2. Do not convert the current D2 FAIL into PASS by retroactively collapsing same-family variants.
3. Permit a separately pre-registered `D2_FAMILY_CLUSTERED_V0` study as a new method candidate, subject to reviewer or owner approval before it can affect readiness.
4. Continue independent-family candidate research until a genuinely different edge survives first-pass gates.
5. Proceed only with dry-run and cost measurement evidence while marking Phase 2 paper execution as not authorized.

## Next Action

Do not tune `breakout_retest` or the same-family alternatives to force D2. The next implementation step, if approved, is a family-assignment table and `D2_FAMILY_CLUSTERED_V0` report generator that leaves the current candidate-level D2 report unchanged.
