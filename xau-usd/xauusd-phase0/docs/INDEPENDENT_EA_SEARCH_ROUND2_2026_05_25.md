# Independent EA Search Round 2

Generated: 2026-05-25

## Starting Point

The previous two independent attempts were useful but rejected:

| Candidate | Result | Reason |
| --- | --- | --- |
| `gold_fx_proxy_divergence_v0` | `REJECTED_FIRST_PASS` | Broker-consistent proxy data was acquired, but 0/9 PF cells reached 1.30. |
| `h1_smooth_trend_exhaustion_reversal_v0` | `REJECTED_FIRST_PASS` | XAU-only H1 exhaustion reversal had enough trades, but 0/9 PF cells reached 1.30. |

This round should not tune either rejected v0. The next lane must use a distinct information source.

## Selected Lane

`xau_xag_relative_value_v0`

Core idea:

```text
Gold/silver relative-value stress may identify precious-metals flow that is not visible in XAUUSD alone. If XAUUSD diverges strongly from XAGUSD and then confirms relative reversion or continuation on H1, the pair relationship may provide an independent signal family.
```

Why this is independent:

- It is precious-metals relative value, not a level/retest system.
- It does not use round numbers, session extremes, pivots, sweeps, VWAP, inside days, outside days, or prior high/low reclaims.
- It uses a new cross-symbol information source, XAGUSD, not the EURUSD/USDJPY broad-USD proxy that just failed.
- It can be falsified cleanly under the same 9-cell Phase 0 process once data exists.

## Data Status

`XAGUSD` was not present in the local symbol config or data tree at the start of this round.

The config now includes `XAGUSD` so raw broker exports can be normalized. Capital.com, Pepperstone, and Dukascopy XAGUSD H1 data have been acquired and normalized. The XAGUSD readiness gate now passes.

## Required Data

| Broker | Symbol | Timeframe | Required window |
| --- | --- | --- | --- |
| capital_com | XAGUSD | H1 | Present locally |
| pepperstone | XAGUSD | H1 | Present locally |
| dukascopy | XAGUSD | H1 | Present locally |

Strict rule:

```text
Do not substitute Dukascopy or Pepperstone XAGUSD data into Capital.com cells.
```

## Machine Checks

Readiness command:

```powershell
.\.venv\Scripts\phase0.exe generate-xau-xag-relative-data-readiness
```

Export presets:

```text
mt5/xau_xag_relative_value_export_presets/
```

Tracked requirement file:

```text
docs/XAU_XAG_RELATIVE_VALUE_V0_DATA_REQUIREMENTS.csv
docs/XAU_XAG_RELATIVE_VALUE_V0_DATA_ACQUISITION_LOG.md
```

## First-Pass Result

`xau_xag_relative_value_v0` was implemented as a research-only strategy, smoke-tested, and run through the real 9-cell matrix.

Result: `REJECTED_FIRST_PASS`

Reason: 0/9 cells reached PF >= 1.30. Trade count was adequate at 102 to 107 trades per cell, so this was an expectancy failure rather than a data-frequency blocker.

Full result:

```text
docs/XAU_XAG_RELATIVE_VALUE_V0_FIRST_PASS.md
```

## Process Boundary

Do not proceed to deciles, multisymbol, intrabar, or Gate 9 for this version.

Do not tune `xau_xag_relative_value_v0` in place. Any future XAU/XAG relative-value revisit needs a new versioned hypothesis and fresh first pass.

This lane does not alter active Phase 1 soak, Phase 2 readiness, approved expert status, dry-run permission, or trade permissions.
