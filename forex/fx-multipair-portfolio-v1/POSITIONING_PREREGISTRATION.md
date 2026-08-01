# US500 Positioning & Skew — Preregistration

Status: `PREREGISTERED_BEFORE_ANY_RESULT`
Written 2026-08-01, before the data was downloaded.

## Why this lane exists

Six independent price-pattern approaches on US500 have failed (bar-geometry
families, overnight effect, daily reversal plus nine refinements, a
14,400-attempt search whose survivors matched sign-flipped noise, the corrected
search at holdout PF 1.009, and walk-forward at −390 over five forward years).

Every one used only price. This lane uses information price does not contain:
**who is positioned how**, and **what the options market charges for tail risk**.
That is the only remaining honest direction, and it is being tested because it is
a different input, not because the previous answers were unsatisfying.

## Data

**Positioning — CFTC Traders in Financial Futures**, contract `13874+`
(S&P 500 Consolidated). Fields: dealer, asset-manager and leveraged-fund
long/short/spread positions, weekly.

**Skew and volatility — CBOE indices**: `^SKEW` (implied tail risk priced from
OTM puts), `^VIX`, `^VIX3M`, `^VVIX`, `^VIX9D`. Daily.

## The publication-lag rule — non-negotiable

The COT report snapshots positions on **Tuesday** and is released **Friday
15:30 ET**. Using Tuesday's data any earlier is look-ahead and would invent an
edge that cannot be traded.

Every positioning signal is therefore lagged to the **following Monday open**,
a full trading day after public release. No exceptions, and the lag is applied
in the loader rather than in each test so it cannot be forgotten.

CBOE indices are same-day close values and are used with a one-day lag.

## Hypotheses, fixed now

**P1 — Speculator crowding is contrarian.** Leveraged-fund net positioning at a
multi-year extreme precedes mean reversion. Long-documented; leveraged funds are
trend-followers and their crowding marks exhaustion.

**P2 — Dealer positioning is the mirror of customer demand.** Dealers take the
other side of customer flow, so extreme dealer net short implies crowded
customer length. Tested as a contrarian signal.

**P3 — Asset-manager positioning is *not* contrarian.** Asset managers are slow,
benchmark-driven and generally right on trend. Included as a directional control
that should behave differently from P1/P2; if all three behave identically the
signal is just market beta.

**P4 — SKEW.** High `^SKEW` means expensive crash protection. Tested both
directions with no prior committed, because the literature disagrees.

**P5 — VIX term structure.** `VIX/VIX3M` above 1 (backwardation) marks acute
stress and historically precedes bounces.

## Test protocol

Forward horizons of 1, 2 and 4 weeks on US500 (Dukascopy CFD closes, 2016–2023,
the same 8 years used throughout this project).

Design 2016–2020, holdout 2021–2023. The holdout contains 2022, and is read
once.

Significance is judged on **non-overlapping** samples: a 4-week horizon uses
every 4th observation. Overlapping weekly windows inflate t-statistics badly and
that is how positioning studies usually go wrong.

## Gates

A hypothesis survives only if:

- the design effect exceeds 2 standard errors on non-overlapping samples;
- the sign is unchanged in the holdout;
- the effect is larger than the round-trip cost of ~0.9 index points; and
- it is not reproduced by the equivalent test on **shuffled** positioning data,
  which is run as a null exactly as the mega-search null was.

Weekly data over 8 years gives roughly 400 observations, or ~100
non-overlapping ones at the 4-week horizon. That is a small sample and the
gates are set accordingly — a marginal t-statistic here is not evidence.

## Declared in advance

If P1–P5 all fail, the conclusion is that positioning and skew do not provide a
tradeable US500 edge at weekly frequency on free public data, and this lane
closes like the others. No sixth variant will be constructed to rescue it.
