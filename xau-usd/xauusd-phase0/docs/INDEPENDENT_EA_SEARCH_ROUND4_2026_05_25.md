# Independent EA Search Round 4

Generated: 2026-05-25

## Starting Point

The latest independent lanes were rejected:

| Candidate | Result | Reason |
| --- | --- | --- |
| `xau_xag_relative_value_v0` | `REJECTED_FIRST_PASS` | Broker-consistent XAGUSD data was acquired, but 0/9 PF cells reached 1.30. |
| `h1_return_autocorrelation_state_v0` | `REJECTED_FIRST_PASS` | H1 modeled return-state produced enough trades, but 0/9 PF cells reached 1.30. |

This round should not tune any rejected v0. The next lane must use a distinct information source.

## Selected Lane

`h1_m5_path_skew_reversal_v0`

Core idea:

```text
The internal M5 path of a completed H1 candle may reveal late absorption that is invisible in H1-only indicators. If a wide H1 bar moves strongly one way early, but the final third of its M5 path reverses, the next hours may mean-revert.
```

Why this is independent:

- It uses sub-hour path formation, not H1 autocorrelation, XAGUSD, FX proxies, or fixed price levels.
- It does not use round numbers, session extremes, pivots, sweeps, VWAP, inside days, outside days, or prior high/low reclaims.
- It is a microstructure-style proxy using existing M5 and H1 bars.
- It can be falsified cleanly under the existing 9-cell process.

## Required Data

No new data is required. The candidate uses existing XAUUSD H1 decision bars and M5 execution/path bars across the standard 9-cell matrix.

## Machine Checks

Hypothesis file:

```text
docs/hypothesis_h1_m5_path_skew_reversal_v0.md
```

Research boundary:

```text
Research-only candidate. It must be run through explicit research commands and must not enter the active `all` expert set.
```

## First-Pass Result

`h1_m5_path_skew_reversal_v0` was implemented as a research-only strategy, smoke-tested, and run through the real 9-cell matrix.

Result: `REJECTED_FIRST_PASS`

Reason: 0/9 cells reached PF >= 1.30. Trade count was high at 498 to 644 trades per cell, so this was an expectancy failure rather than a data-frequency blocker.

Full result:

```text
docs/H1_M5_PATH_SKEW_REVERSAL_V0_FIRST_PASS.md
```

## Process Boundary

Do not proceed to deciles, multisymbol, intrabar, or Gate 9 for this version.

Do not tune this candidate in place after first-pass results. Any future revisit needs a new versioned hypothesis and fresh SHA256 lock.

This lane does not alter active Phase 1 soak, Phase 2 readiness, approved expert status, dry-run permission, or trade permissions.
