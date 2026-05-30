# Independent EA Search Round 34

Generated: 2026-05-30

## Starting Point

Round 33 rejected the H1 VIX/VXV term-structure inversion reversal candidate. Round 34 tested the paired opposite interpretation: if term-structure inversion is not an exhaustion signal, it might be a continuation signal when XAU trend confirmation agrees.

## Selected Lane

`h1_vix_term_structure_inversion_followthrough_v0`

Core idea:

```text
Use shifted VIX/VXV term-structure inversion as an equity-risk stress proxy, then follow completed H1 XAU direction only when the completed H1 candle confirms continuation.
```

Why this is process-safe:

- It is a fresh versioned v0 hypothesis.
- It is independent of the breakout-retest / level-and-pullback family.
- It does not tune the rejected reversal candidate; it tests the opposite pre-registered mechanism.
- It uses official public FRED `VIXCLS` and `VXVCLS` data.
- It was SHA256-locked before its result-producing matrix run.
- It stays in the research registry only and does not alter MT5 runtime, demo observers, or trade permissions.

## Machine Checks

Hypothesis file:

```text
docs/hypothesis_h1_vix_term_structure_inversion_followthrough_v0.md
```

Research hash:

```text
89157f81ac11345de02b0292fd8f6558eb53075de8ff921ee6131babeb7b7c47
```

Synthetic smoke:

```text
PASS - 4 synthetic signals, market trade plan generated, active registry disabled.
```

Real 9-cell matrix:

```text
REJECTED_FIRST_PASS - 897 total cost-cell trades, 9/9 trade-count cells, but 0/9 PF cells reached 1.30. Best PF was 1.0207.
```

First-pass report:

```text
docs/H1_VIX_TERM_STRUCTURE_INVERSION_FOLLOWTHROUGH_V0_FIRST_PASS.md
```

## Process Boundary

Do not tune this candidate in place after first-pass results. This lane does not alter active Phase 1/Phase 3 observation, Phase 2 readiness, approved expert status, dry-run permission, demo observer authority, or trade permissions.
