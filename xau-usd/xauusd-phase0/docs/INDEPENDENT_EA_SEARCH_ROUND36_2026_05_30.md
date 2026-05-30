# Independent EA Search Round 36

Generated: 2026-05-30

## Starting Point

Round 35 rejected H1 policy-uncertainty intraday reversal. Round 36 tested a separate macro-price input: shifted US breakeven-inflation shocks from FRED.

## Selected Lane

`h1_breakeven_inflation_shock_reversal_v0`

Core idea:

```text
Use shifted FRED T5YIE/T10YIE breakeven-inflation shocks to identify XAU H1 short-term overreaction, then trade only after a completed H1 reversal candle.
```

Why this is process-safe:

- It is a fresh versioned v0 hypothesis.
- It is independent of the breakout-retest / level-and-pullback family.
- It does not tune the rejected H4 breakeven-inflation momentum candidate; it tests a different H1 reversal mechanism.
- It uses public FRED `T5YIE` and `T10YIE` data already available locally with full matrix coverage.
- It was SHA256-locked before its result-producing matrix run.
- It stays in the research registry only and does not alter MT5 runtime, demo observers, or trade permissions.

## Machine Checks

Hypothesis file:

```text
docs/hypothesis_h1_breakeven_inflation_shock_reversal_v0.md
```

Research hash:

```text
fc043d75f1f22bccdf5763f1cdb7d52e8102bb8eac6ab8f16aa7bc6f069625a7
```

Synthetic smoke:

```text
PASS - 1 synthetic signal, market trade plan generated, active registry disabled.
```

Real 9-cell matrix:

```text
REJECTED_FIRST_PASS - 855 total cost-cell trades, 9/9 trade-count cells, 0/9 PF cells reached 1.30. Best PF was 0.8992.
```

First-pass report:

```text
docs/H1_BREAKEVEN_INFLATION_SHOCK_REVERSAL_V0_FIRST_PASS.md
```

## Process Boundary

Do not tune this candidate in place after first-pass results. This lane does not alter active Phase 1/Phase 3 observation, Phase 2 readiness, approved expert status, dry-run permission, demo observer authority, or trade permissions.
