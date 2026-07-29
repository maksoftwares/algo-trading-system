# EURUSD Neutral Subregime Experts Preregistration

Frozen at UTC: 2026-07-29T13:42:02.2212627Z

Status: `FROZEN_BEFORE_FIRST_COMBINED_OUTCOME_RUN`

Boundary: research only. No broker, terminal, account, order, or position access is authorized.

## Hypothesis

The earlier Regime 1 classifier may be too broad. A single Neutral expert is forced to mix low-volatility compression, range extremes, directional drift, and macro-pressure states. This test divides only the causal Neutral inventory into six rolling outcome-blind H4 subregimes and assigns each subregime at most one simple specialist using only prior closed outcomes.

All archived history is development data. This is a strict causal walk-forward replay, not pristine untouched out-of-sample evidence.

## Frozen Architecture

- Source: 7,150 Neutral H4 decisions, each with frozen long and short exact-cost outcomes.
- Geometry: 0.75 H4 ATR stop, 1.50R target, 12-H4-bar maximum hold, exact M5 bid/ask, 0.7-pip spread floor, 0.1-pip adverse slippage per side, stop first, and another 0.5-pip stress.
- Monthly training: trailing three years; both side outcomes must close before the monthly boundary.
- Subregimes: six KMeans clusters using only H4 range, volatility ratio, efficiency, six- and 24-bar returns, prior-range location, and lagged macro pressure.
- Scaling and clustering are refit only on the prior training window.
- Cluster numbers are deterministically ranked by their standardized centroids, without outcomes.

## Frozen Specialists

Ten fixed experts cover one- and three-bar fades, three- and six-bar follow-through, prior-24-bar extreme fade/follow, H4 body fade/follow, and macro-pressure fade/follow. Each rule has one fixed feature, threshold, and sign mapping in the frozen config.

For each subregime and month, an expert is admitted only with at least 24 prior non-overlapping trades, at least eight in each training half, base PF at least 1.15, stressed PF at least 1.05, positive total R, and PF above 1.0 in both halves. The winner is ranked by stressed PF, then worst-half PF, then sample size. No qualifying expert means cash.

## Validation Gates

The combined 2020 through June 2026 walk-forward must have at least 60 trades, 45%-55% wins, payoff 1.35-1.75, PF at least 1.30, stressed PF at least 1.15, every chronological block profitable, latest-12-month PF at least 1.15 and positive, at least 55% positive active months, best-5%-removed PF at least 1.0, and drawdown no more than 15R.

Both directions need at least ten trades and PF at least 0.90. No expert or subregime may supply more than 60% of trades.

No cluster count, feature, expert, threshold, direction mapping, training length, admission gate, year, or concentration rule may change after the result. A historical pass cannot authorize demo or live trading.

## Mechanical Amendment 1

The first execution stopped before producing selections, trades, or P&L because a zero-trigger expert/subregime produced an empty frame without a `signal_time_utc` column. The diagnostics now return zero trades, zero PF, zero R, and `admitted=false` for an empty training frame. No trading, clustering, expert, threshold, ranking, admission, cost, reporting, or quality-gate rule changed. The implementation and test locks retain both the original and amended hashes.
