# Independent EA Search Round 24

Generated: 2026-05-25

## Starting Point

Round 23 produced the strongest independent macro evidence so far, but `h4_macro_composite_risk_state_v0` still failed because Capital.com had only 34 trades and all concentration/activity gates failed. A new versioned hypothesis was required for any follow-up.

## Selected Lane

`h4_macro_composite_risk_state_v1`

Core idea:

```text
Keep the same transparent fixed macro vote table as v0, but allow a long/short state at net score +/-2 when at least three same-side macro families agree.
```

Why this is process-safe:

- v0 remains rejected and unchanged.
- v1 has a new name, new hypothesis, and new SHA256 lock before any smoke or matrix run.
- The fixed vote families are still transparent and not machine-optimized.

## Machine Checks

Hypothesis file:

```text
docs/hypothesis_h4_macro_composite_risk_state_v1.md
```

Synthetic smoke:

```text
PASS - 20 synthetic signals, market trade plans generated, active registry disabled.
```

Real 9-cell matrix:

```text
REJECTED_FIRST_PASS - 51 to 169 trades per cell, 3/9 PF cells reached 1.30, sample size passed, but all PF-passing cells were Pepperstone-only and concentration/activity failed.
```

First-pass report:

```text
docs/H4_MACRO_COMPOSITE_RISK_STATE_V1_FIRST_PASS.md
```

## Process Boundary

Do not tune this candidate in place after first-pass results. Any future macro-composite revisit needs a new versioned hypothesis and fresh SHA256 lock.

This lane does not alter active Phase 1 soak, Phase 2 readiness, approved expert status, dry-run permission, or trade permissions.
