# Independent EA Search Brief

Generated: 2026-05-25

## Search Boundary

The current evidence base already tested 39 candidate families or variants. The only approved edge family remains level-and-pullback / breakout-retest. Same-family retest variants may be useful for observation, but they do not solve diversification.

This search therefore excludes:

- tuning rejected v0 candidates in place
- renaming retest, reclaim, round-number, or session-extreme variants as independent EAs
- adding marketplace or black-box MT5 EAs
- lowering Phase 0 gates to rescue weak candidates

The target is a mechanically distinct research lane that can be pre-registered, data-audited, and tested under the same Phase 0 rules.

## Candidate Families Reviewed

| Candidate family | Independence | Data state | Decision |
| --- | --- | --- | --- |
| Gold-FX proxy relative strength | High | Needs synchronized cross-symbol H1 data across matrix venues | Selected as first new candidate. |
| XAU/XAG relative value | High | Requires XAGUSD bars and symbol cost model | Parked until silver data exists. |
| Scheduled macro-event behavior | High | Requires audited economic calendar/event labels | Parked until event data exists. |
| Measured-spread microstructure regime | Medium | Spread logger exists, but signal would be broker-specific | Use later as filter/review input, not first standalone EA. |
| Another XAU-only candle/session pattern | Low | Data exists | Deprioritized because many similar variants already failed. |

## Selected Candidate

First new independent candidate:

```text
gold_fx_proxy_divergence_v0
```

Core idea:

```text
Gold sometimes shows persistent relative strength or weakness against broad USD pressure. If XAUUSD rises despite USD strength, or falls despite USD weakness, that divergence may identify non-FX gold flow strong enough to continue for several hours.
```

Why this is independent:

- It is intermarket-relative, not level-and-pullback.
- It does not use prior highs/lows, retests, round numbers, session extremes, pivots, or sweep/reclaim logic.
- It requires synchronized FX proxy data, so it tests a new information class rather than another XAU-only candle pattern.
- It can be falsified cleanly if the edge disappears across brokers, costs, or non-Capital.com venues.

## Data Requirement

Minimum viable research data:

| Series | Timeframe | Purpose |
| --- | --- | --- |
| XAUUSD | H1, M5 | Target symbol and execution simulation. |
| EURUSD | H1 | USD proxy component, inverted. |
| USDJPY | H1 | USD proxy component. |

Preferred later upgrade:

| Series | Timeframe | Purpose |
| --- | --- | --- |
| DXY or USD index CFD | H1 | Cleaner broad USD proxy. |
| XAGUSD | H1 | Precious-metals relative confirmation. |
| US yields / real-yield proxy | H1 or D1 | Macro confirmation, separate later candidate family. |

Current local data has Capital.com EURUSD/USDJPY, but the full 9-cell matrix needs a venue-consistent cross-symbol data plan before this candidate can produce authoritative results.

Feasibility pass from the current processed-bar tree:

| Broker | XAUUSD H1 | EURUSD H1 | USDJPY H1 | Research status |
| --- | --- | --- | --- | --- |
| capital_com | Present | Present | Present | Enough for exploratory loader design only. |
| pepperstone | Present | Missing | Missing | Blocks venue-consistent matrix cells 4-6. |
| dukascopy | Present | Missing | Missing | Blocks venue-consistent matrix cells 7-9. |

## Immediate Output

Created a locked hypothesis draft:

```text
docs/hypothesis_gold_fx_proxy_divergence_v0.md
```

Current status after registration, data acquisition, and first-pass matrix:

```text
REJECTED_FIRST_PASS
```

The data blocker was cleared with broker-consistent proxy inputs, but the locked v0 failed the matrix edge gate: 0 of 9 PF cells reached 1.30. This remains a useful audited rejection and does not contaminate the active Phase 1 soak or Phase 2 readiness gates.

## Parallel Candidate

Second independent candidate:

```text
h1_smooth_trend_exhaustion_reversal_v0
```

Why it exists now:

- It is XAU-only and can proceed while the proxy-divergence candidate waits on missing Pepperstone/Dukascopy EURUSD and USDJPY exports.
- It uses 24-hour H1 trend efficiency, EMA/ATR stretch, and a completed H1 reversal candle.
- It does not use round numbers, session extremes, sweeps, VWAP, pivots, inside days, outside days, retests, or cross-symbol input.
- It remains research-only unless it survives the normal Phase 0 gates.

First-pass result:

```text
REJECTED_FIRST_PASS
```

The candidate produced 42-77 trades per matrix cell, but 0 of 9 cells reached PF 1.30. It should not be tuned under the same version.

## Next Research Steps

1. Add cross-symbol data availability checks for H1 EURUSD/USDJPY by broker and cell window.
2. Decide whether the Phase 0 matrix can use Capital.com-only FX proxy as exploratory evidence or must wait for Pepperstone and Dukascopy FX bars.
3. Implement the research-only strategy only after the data contract is accepted.
4. Run synthetic smoke first, then a research matrix, then deciles/multisymbol only if the matrix survives.
5. Keep `breakout_retest` as the only Phase 2 execution-eligible stream unless this new candidate later passes the full process.

Blocker fix package:

```text
docs/GOLD_FX_PROXY_DIVERGENCE_V0_BLOCKER_FIX.md
docs/GOLD_FX_PROXY_DIVERGENCE_V0_DATA_REQUIREMENTS.csv
docs/GOLD_FX_PROXY_DIVERGENCE_V0_DATA_ACQUISITION_LOG.md
docs/GOLD_FX_PROXY_DIVERGENCE_V0_FIRST_PASS.md
```
