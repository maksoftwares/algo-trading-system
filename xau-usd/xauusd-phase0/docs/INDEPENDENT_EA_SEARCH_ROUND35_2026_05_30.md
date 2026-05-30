# Independent EA Search Round 35

Generated: 2026-05-30

## Starting Point

Round 34 rejected the H1 VIX/VXV term-structure inversion followthrough lane. Round 35 moved away from volatility term structure and tested whether shifted daily US policy-uncertainty shocks create H1 XAU overreaction/reversal opportunities.

## Selected Lane

`h1_policy_uncertainty_intraday_reversal_v0`

Core idea:

```text
Use shifted FRED USEPUINDXD daily policy-uncertainty shocks to identify XAU H1 short-term overreaction, then trade only after a completed H1 reversal candle.
```

Why this is process-safe:

- It is a fresh versioned v0 hypothesis.
- It is independent of the breakout-retest / level-and-pullback family.
- It does not tune the rejected H4 policy-uncertainty safe-haven candidate; it tests the opposite intraday reversal mechanism.
- It uses public FRED `USEPUINDXD` data already available locally with full matrix coverage.
- It was SHA256-locked before its result-producing matrix run.
- It stays in the research registry only and does not alter MT5 runtime, demo observers, or trade permissions.

## Machine Checks

Hypothesis file:

```text
docs/hypothesis_h1_policy_uncertainty_intraday_reversal_v0.md
```

Research hash:

```text
b48ce75fca4f650d3f0b5c30fbe795fcca621c391a2334c70eef3f3e0656f74c
```

Synthetic smoke:

```text
PASS - 1 synthetic signal, market trade plan generated, active registry disabled.
```

Real 9-cell matrix:

```text
REJECTED_FIRST_PASS - 366 total cost-cell trades, 6/9 trade-count cells, 0/9 PF cells reached 1.30. Best PF was 1.1320.
```

First-pass report:

```text
docs/H1_POLICY_UNCERTAINTY_INTRADAY_REVERSAL_V0_FIRST_PASS.md
```

## Process Boundary

Do not tune this candidate in place after first-pass results. This lane does not alter active Phase 1/Phase 3 observation, Phase 2 readiness, approved expert status, dry-run permission, demo observer authority, or trade permissions.
