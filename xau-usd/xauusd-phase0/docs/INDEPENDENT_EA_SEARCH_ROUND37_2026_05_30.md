# Independent EA Search Round 37

Generated: 2026-05-30

## Starting Point

Round 36 rejected H1 breakeven-inflation shock reversal. Round 37 tested a separate rates input: shifted Treasury-rate and curve shocks from FRED.

## Selected Lane

`h1_treasury_curve_shock_reversal_v0`

Core idea:

```text
Use shifted FRED DGS2/DGS10/T10Y2Y rate and curve shocks to identify XAU H1 short-term overreaction, then trade only after a completed H1 reversal candle.
```

Why this is process-safe:

- It is a fresh versioned v0 hypothesis.
- It is independent of the breakout-retest / level-and-pullback family.
- It does not tune the rejected H4 Treasury-curve momentum candidate; it tests a different H1 reversal mechanism.
- It uses public FRED `DGS2`, `DGS10`, and `T10Y2Y` data already available locally with full matrix coverage.
- It was SHA256-locked before its result-producing matrix run.
- It stays in the research registry only and does not alter MT5 runtime, demo observers, or trade permissions.

## Machine Checks

Hypothesis file:

```text
docs/hypothesis_h1_treasury_curve_shock_reversal_v0.md
```

Research hash:

```text
4eb54959e60c769e27bda70fd9023d99d751419915e89a4d70b440b5132cfa6e
```

Synthetic smoke:

```text
PASS - 1 synthetic signal, market trade plan generated, active registry disabled.
```

Real 9-cell matrix:

```text
REJECTED_FIRST_PASS - 558 total cost-cell trades, 9/9 trade-count cells, 0/9 PF cells reached 1.30, and max zero-trade months reached 10.
```

First-pass report:

```text
docs/H1_TREASURY_CURVE_SHOCK_REVERSAL_V0_FIRST_PASS.md
```

## Process Boundary

Do not tune this candidate in place after first-pass results. This lane does not alter active Phase 1/Phase 3 observation, Phase 2 readiness, approved expert status, dry-run permission, demo observer authority, or trade permissions.
