# Independent EA Search Round 25

Generated: 2026-05-26

## Starting Point

Round 24 widened the fixed macro-composite vote and fixed the sample-size problem, but `h4_macro_composite_risk_state_v1` still failed with Pepperstone-only strength. A fresh, mechanically distinct macro lane was required before trying more.

## Selected Lane

`h4_policy_uncertainty_safe_haven_v0`

Core idea:

```text
Use public FRED US Economic Policy Uncertainty data as a slow H4/D1 safe-haven state. Trade XAUUSD only when policy-uncertainty acceleration agrees with the local H4 return and range context.
```

Why this is process-safe:

- It uses a new FRED input family, `USEPUINDXD`, not the rejected macro-composite vote.
- It has a new name, new hypothesis, and new SHA256 lock before any smoke or matrix run.
- The rules are fixed and transparent; no rejected v0 was tuned in place.

## Machine Checks

Hypothesis file:

```text
docs/hypothesis_h4_policy_uncertainty_safe_haven_v0.md
```

Synthetic smoke:

```text
PASS - 20 synthetic signals, market trade plans generated, active registry disabled.
```

Real 9-cell matrix:

```text
REJECTED_FIRST_PASS - 142 to 181 trades per cell, 3/9 PF cells reached 1.30, sample size/activity/cost sensitivity passed, but all PF-passing cells were Pepperstone-only and concentration failed in Capital.com and Dukascopy.
```

First-pass report:

```text
docs/H4_POLICY_UNCERTAINTY_SAFE_HAVEN_V0_FIRST_PASS.md
```

## Process Boundary

Do not tune this candidate in place after first-pass results. Any future policy-uncertainty or macro-stress revisit needs a new versioned hypothesis and fresh SHA256 lock.

This lane does not alter active Phase 1 soak, Phase 2 readiness, approved expert status, dry-run permission, or trade permissions.
