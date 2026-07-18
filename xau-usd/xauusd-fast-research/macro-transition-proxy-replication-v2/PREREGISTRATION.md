# XAUUSD Macro Transition Proxy Replication V2 Preregistration

## Purpose

This package performs one untouched-period replication of the fixed transition
candidate selected after the Macro-Regime Routing V1 campaign. It is a
replication, not a new parameter search. The tested candidate is V1 attempt
23925, variant `00e072837bf6f6e2`.

The exact Dukascopy US Treasury index has no usable tick history before January
2019. The replication therefore substitutes two independently declared liquid
US Treasury total-return proxies while keeping the gold regime, direction,
signal thresholds, stop, target, maximum holding time, execution model, and
cost stress unchanged:

- `TLT.US-USD`, iShares 20+ Year Treasury Bond ETF CFD.
- `IEF.US-USD`, iShares 7-10 Year Treasury Bond ETF CFD.

Both proxy tests are fixed before any trade result is opened. No proxy may be
dropped because it performs poorly.

## Frozen evaluation window

- TLT: 2017-12-01 00:00 UTC through 2019-01-21 00:00 UTC, end exclusive.
- IEF: 2018-02-01 00:00 UTC through 2019-01-21 00:00 UTC, end exclusive.
- The V1 discovery window began in July 2019, so these gold outcomes are
  temporally untouched by that campaign.

## Fixed source and feature translation

- Gold execution and regime data use the already verified Dukascopy native
  bid/ask M5 cache aggregated to complete M15/H4 bars.
- DXY, TLT, and IEF use official keyless Dukascopy Jetta tick payloads.
- Only weekday UTC hours 13 through 20 are requested. This interval contains
  the full 09:30-16:00 New York ETF session in both standard and daylight time.
- Tick payloads are validated, gzip-compressed, retained, and SHA-256 hashed.
- Dukascopy DXY hour 2017-12-13 16:00 UTC contains one crossed bid/ask tick.
  The complete raw hour is retained and hashed in quarantine, but all of its
  M15 buckets are excluded. Returns spanning the resulting gap are invalid.
- M15 proxy closes use the last observed tick midpoint in each M15 bucket.
- H1 returns require an exact one-hour timestamp difference.
- The V1 `D2` denominator is translated to the prior 48 clock hours of
  available H1-return observations, excluding the current observation, with a
  minimum of 20 observations. This time-based translation is necessary because
  the ETF proxies trade 6.5 hours per day rather than nearly around the clock.
- DXY pressure is the negative standardized DXY H1 return. Bond pressure is the
  positive standardized ETF H1 return.
- Features at time T use no data after T.

## Fixed candidate

- Regime owner: `TRANSITION`.
- Mechanic: `TRANS_ANCESTRY_MACRO_REACCELERATION`.
- Regime: `TRANSITION_UNKNOWN` only; `UNSAFE_SHOCK` remains abstain.
- Transition age: at most 48 M15 bars.
- Direction: the last resolved trend direction.
- DXY and bond pressure must agree with that ancestry direction.
- Absolute pressure threshold: 0.50 for both inputs.
- Gold H1 alignment: from -1.50 ATR through +0.25 ATR, inclusive.
- Candle body fraction: at least 0.20.
- Candle-direction confirmation: not required.
- Stop: 1.75 ATR.
- Target: 2.00R.
- Maximum holding time: 18 hours.
- Maximum four entries per UTC day and no overlapping position per proxy test.

## Registered interpretation gates

Each proxy must independently have:

- At least 8 executed trades.
- Positive stress net R.
- Stress profit factor at least 1.10.
- Average stress return at least +0.02R.
- Nonnegative stress net R after removing its two best trades.
- Closed-trade drawdown no greater than 10R.

The pooled unique gold-trade evidence, with duplicate proxy signals on the same
gold event counted once, must have:

- At least 16 trades.
- Stress profit factor at least 1.25.
- Average stress return at least +0.05R.
- Positive stress net R after removing its three best trades.
- Closed-trade drawdown no greater than 12R.

Passing is supporting replication evidence only. It does not authorize model
training, demo execution, or live execution. Exact source confirmation on the
original Treasury instrument where available and prospective shadow evidence
remain required. Failure or insufficient sample closes this exact proxy
replication; it does not authorize same-version tuning.

## Research controls

- Candidate count is exactly two and parameter count is exactly one per proxy.
- There is no model fitting, threshold search, walk-forward selection, or
  post-outcome fallback.
- The single declared source-hour quarantine is a pre-outcome data-integrity
  rule and may not be expanded after replication outcomes are opened.
- Paid data is forbidden. Databento is not used.
- Account or broker actions are forbidden.
- Same-bar stop/target collisions are resolved stop-first.
- Historical results are research evidence, not a profit promise.
