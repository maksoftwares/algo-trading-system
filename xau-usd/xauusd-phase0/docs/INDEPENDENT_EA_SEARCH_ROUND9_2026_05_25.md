# Independent EA Search Round 9

Generated: 2026-05-25

## Starting Point

Round 8 rejected the M15 two-bar exhaustion reversal candidate. It produced enough trades but no PF survival, so the reversal/fade interpretation is not an EA.

## Selected Lane

`m15_two_bar_impulse_continuation_v0`

Core idea:

```text
Follow unusually sharp completed two-bar M15 acceleration and test whether short-horizon continuation exists without using levels, sessions, VWAP, or cross-symbol inputs.
```

Why this is independent:

- It uses completed M15 impulse structure only, not retests, round numbers, session extremes, VWAP, or intermarket proxies.
- It directly tests impulse persistence rather than the rejected snapback hypothesis, with separate locked direction and trade-plan geometry.
- It can be falsified under the existing 9-cell matrix with existing XAUUSD M15 and M5 data.

## Required Data

No new data is required. The candidate uses existing XAUUSD M15 feature bars and M5 execution bars across the standard 9-cell matrix.

## Machine Checks

Hypothesis file:

```text
docs/hypothesis_m15_two_bar_impulse_continuation_v0.md
```

Research boundary:

```text
Research-only candidate. It must be run through explicit research commands and must not enter the active `all` expert set.
```

Synthetic smoke:

```text
PASS - 1 synthetic signal, market trade plan generated, active registry disabled.
```

Real 9-cell matrix:

```text
REJECTED_FIRST_PASS - 1192 to 1310 trades per cell, but 0/9 PF cells reached 1.30 and catastrophic loss failed in five cells.
```

First-pass report:

```text
docs/M15_TWO_BAR_IMPULSE_CONTINUATION_V0_FIRST_PASS.md
```

## Process Boundary

Do not tune this candidate in place after first-pass results. Any future revisit needs a new versioned hypothesis and fresh SHA256 lock.

This lane does not alter active Phase 1 soak, Phase 2 readiness, approved expert status, dry-run permission, or trade permissions.
