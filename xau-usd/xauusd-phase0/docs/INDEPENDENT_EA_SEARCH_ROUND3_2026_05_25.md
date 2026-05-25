# Independent EA Search Round 3

Generated: 2026-05-25

## Starting Point

The last independent lanes were useful but rejected:

| Candidate | Result | Reason |
| --- | --- | --- |
| `gold_fx_proxy_divergence_v0` | `REJECTED_FIRST_PASS` | Broker-consistent FX proxy data was acquired, but 0/9 PF cells reached 1.30. |
| `h1_smooth_trend_exhaustion_reversal_v0` | `REJECTED_FIRST_PASS` | H1 XAU-only exhaustion reversal produced enough trades, but 0/9 PF cells reached 1.30. |
| `xau_xag_relative_value_v0` | `REJECTED_FIRST_PASS` | Broker-consistent XAGUSD data was acquired, but 0/9 PF cells reached 1.30. |

This round should not tune any rejected v0. The next lane must use a distinct information source.

## Selected Lane

`h1_return_autocorrelation_state_v0`

Core idea:

```text
XAUUSD may occasionally enter an H1 return-persistence state where completed hourly returns have positive autocorrelation, directional efficiency, and stable realized volatility. A deterministic modeled-state score can identify those windows without using levels, sessions, or cross-symbol data.
```

Why this is independent:

- It is a return-state model, not a level/retest system.
- It does not use round numbers, session extremes, pivots, sweeps, VWAP, inside days, outside days, or prior high/low reclaims.
- It does not use EURUSD/USDJPY or XAGUSD proxy data.
- It is an auditable first step toward AI-style thinking because the state score is deterministic and hash-lockable.

## Required Data

No new data is required. The candidate uses existing XAUUSD H1 decision bars and M5 execution bars across the standard 9-cell matrix.

## Machine Checks

Hypothesis file:

```text
docs/hypothesis_h1_return_autocorrelation_state_v0.md
```

Research boundary:

```text
Research-only candidate. It must be run through explicit research commands and must not enter the active `all` expert set.
```

## First-Pass Result

`h1_return_autocorrelation_state_v0` was implemented as a research-only strategy, smoke-tested, and run through the real 9-cell matrix.

Result: `REJECTED_FIRST_PASS`

Reason: 0/9 cells reached PF >= 1.30. Trade count was adequate at 148 to 193 trades per cell, so this was an expectancy failure rather than a data-frequency blocker.

Full result:

```text
docs/H1_RETURN_AUTOCORRELATION_STATE_V0_FIRST_PASS.md
```

## Process Boundary

Do not proceed to deciles, multisymbol, intrabar, or Gate 9 for this version.

Do not tune this candidate in place after first-pass results. Any future revisit needs a new versioned hypothesis and fresh SHA256 lock.

This lane does not alter active Phase 1 soak, Phase 2 readiness, approved expert status, dry-run permission, or trade permissions.
