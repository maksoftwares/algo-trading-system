# Independent EA Search Round 32

Generated: 2026-05-30

## Starting Point

Round 31 rejected the GLD/SPY safe-haven rotation followthrough lane. Round 32 revisited an already available external risk-state data class, but tested the opposite mechanism from the rejected VIX reversal attempt.

## Selected Lane

`h4_vix_risk_off_followthrough_v0`

Core idea:

```text
Use shifted daily VIX stress as a broad equity-risk state, then trade H4 XAU followthrough when the local H4 trend and candle confirmation agree.
```

Why this is process-safe:

- It is a fresh versioned v0 hypothesis.
- It is independent of the breakout-retest / level-and-pullback family.
- It does not tune the rejected `h4_vix_risk_off_reversal_v0`; it tests the opposite followthrough behavior.
- It reuses existing local public FRED `VIXCLS` data.
- It was SHA256-locked before its result-producing matrix run.
- It stays in the research registry only and does not alter MT5 runtime, demo observers, or trade permissions.

## Machine Checks

Hypothesis file:

```text
docs/hypothesis_h4_vix_risk_off_followthrough_v0.md
```

Research hash:

```text
f192c592363df866c104f2900bffae9637a73b7f33a6a0fcdbf2325b9b9a7d0a
```

Synthetic smoke:

```text
PASS - 9 synthetic signals, market trade plan generated, active registry disabled.
```

Real 9-cell matrix:

```text
REJECTED_FIRST_PASS - 1,404 total cost-cell trades, 9/9 trade-count cells, max zero-trade months 1, but 0/9 PF cells reached 1.30.
```

First-pass report:

```text
docs/H4_VIX_RISK_OFF_FOLLOWTHROUGH_V0_FIRST_PASS.md
```

## Process Boundary

Do not tune this candidate in place after first-pass results. This lane does not alter active Phase 1/Phase 3 observation, Phase 2 readiness, approved expert status, dry-run permission, demo observer authority, or trade permissions.
