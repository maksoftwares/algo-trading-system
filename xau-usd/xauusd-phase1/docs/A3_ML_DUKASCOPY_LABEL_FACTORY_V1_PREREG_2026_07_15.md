# A3 ML Dukascopy Candidate-Label Factory V1 Preregistration

Date locked: `2026-07-15`

## Purpose

Build the first reusable XAUUSD candidate-label pipeline whose market prices and outcomes come from verified Dukascopy bid/ask ticks rather than MT5 historical prices.

This run has two separate decisions:

1. Is the produced dataset sufficiently complete and causal for ML research?
2. Does the first fixed candidate family show stable standalone trading evidence?

Passing the first decision does not imply passing the second. Neither decision authorizes demo or live execution.

## Frozen Data Boundary

- Source: official Dukascopy Jetta JSON already held by the frozen tick-data foundation.
- Symbol: `XAUUSD`.
- Contiguous period: `2018-07-01T00:00:00Z` through `2024-06-30T23:59:59.999Z`.
- Expected monthly partitions: `72`.
- Every source month must pass the existing acquisition-manifest identity, official-URL, file-existence, and SHA-256 checks.
- H1 Bid and Ask bars are derived directly from each verified raw hourly response.
- Empty market-closed hours remain empty. No bars or ticks are filled or invented.

## Frozen Candidate Family

Family: `dukascopy_h1_symmetric_ema_pullback_v1`.

At the close of a completed UTC H1 bar:

- EMA periods: `20` and `50`.
- EMA slope lag: `5` H1 bars.
- Wilder ATR period: `14`.
- Pullback touch lookback: `3` H1 bars.
- Touch zone: `0.25 ATR` around EMA20 or EMA50.
- Rejection body fraction: at least `0.35`.
- Long close location: at least `0.65`.
- Short close location: at most `0.35`.
- Stop: three-bar swing plus `0.25 ATR` buffer.
- Allowed stop distance: `$3.50` through `$22.00` in XAUUSD price units.
- Target: fixed `2R`.
- Long and short rules are exact mirrors.
- No session, weekday, news, previous-PnL, or MT5-account filter is permitted.

All signal fields use the completed bar and earlier bars only. The entry is the first Dukascopy tick at or after the decision timestamp, provided it arrives within five minutes.

## Frozen Outcome Contract

- Long entry uses Ask; long stop, target, and exit use Bid.
- Short entry uses Bid; short stop, target, and exit use Ask.
- If stop and target occur in the same H1 hour, raw tick order decides the outcome.
- Maximum holding period: `120` hours.
- At the holding deadline, barriers are evaluated through the deadline tick; otherwise the first quote at or after the deadline closes the candidate.
- Maximum timeout-exit grace: `72` hours for a market reopening.
- Fixed size: `0.01` lot with `100` ounces per lot.
- Observed Dukascopy spread is embedded through side-correct entry and exit prices.
- Additional execution stress: `$0.30` per completed candidate.
- Holding-cost stress: `$0.35` per 24 hours, applied pro rata by elapsed holding time.
- Candidates are independent counterfactual labels. They are not a shared-account portfolio simulation.

Primary label: `1` when side-correct P/L after execution and holding stress is positive, otherwise `0`.

The dataset also records gross and stress P/L, gross and stress R, MFE, MAE, duration, exit reason, spread, signal features, split, and source hashes.

## Frozen Splits

- Train: decision time before `2021-07-01T00:00:00Z`.
- Validation: `2021-07-01` through `2023-06-30` UTC.
- Test: `2023-07-01` through `2024-06-30` UTC.

No threshold or family parameter may be changed after inspecting these results. Any change requires a new version and new preregistration.

## Dataset Quality Gates

All must pass:

- Exactly `72` verified source months.
- At least `1,000` candidates.
- At least `99%` of candidates resolve to a side-correct entry and outcome.
- At least `150` resolved rows in each chronological split.
- At least `200` resolved rows in each direction.
- Minority primary-label share at least `20%`.
- No duplicate candidate IDs or decision-time/direction/family keys.
- No candidate uses a future bar or tick in its signal fields.

## Strategy Research Gates

The candidate family is a research survivor only if all pass:

- Train stress PF at least `1.20`.
- Validation stress PF at least `1.20`.
- Test stress PF at least `1.10`.
- Validation average stress R at least `0.05`.
- Test average stress R nonnegative.
- Test maximum closed drawdown no more than `20R`.

These gates evaluate the fixed family only. Passing them would justify deeper portfolio and ML-ranking research, not broker action.

## Prohibited Conclusions

- MT5 historical prices are not ground truth for this run.
- A large tick count is not treated as a large count of independent trades.
- Overlapping candidates are not treated as independent portfolio returns.
- No result is a future-profit guarantee.
- Demo prediction, EA consumption, broker action, and deployment remain disabled.
