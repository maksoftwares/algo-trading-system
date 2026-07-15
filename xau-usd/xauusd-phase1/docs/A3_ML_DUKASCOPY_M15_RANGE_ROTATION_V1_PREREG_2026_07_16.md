# A3 ML Dukascopy M15 Range Rotation V1 Preregistration

Date: `2026-07-16`

## Hypothesis

The rejected M5 campaign used a risk unit that was too small relative to the real Dukascopy XAUUSD spread and imposed one trend-style exit on every regime. A M15 range specialist may have better cost geometry when it targets the already-known range midpoint and places its stop beyond the range excursion.

This is one specialist for one market condition. It is not a universal strategy.

## Outcome-Blind Basis

The train-period opportunity census used no post-entry outcomes. Under the frozen M15 range definition it found approximately `1.16` raw excursions per source day. Approximately `0.78/day` had next-bar spread no greater than `0.33` of a one-ATR reference risk.

No profitability statistic was used to choose the M15 thresholds.

## Data And Firewall

- Consume the hash-locked causal M5 feature cache produced by the prior campaign.
- Aggregate only three complete, contiguous M5 rows into each M15 row.
- Train: 2018-07 through 2020-06.
- Validation: 2020-07 through 2021-06, opened only if the train raw gate passes.
- Internal test: 2021-07 through 2022-06, opened only after a full validation pass.
- Exam: 2022-07 through 2024-06, opened only after a full internal-test pass.

## Specialist Definition

- Range regime: EMA8/EMA32 gap no greater than `0.30 ATR14`, ATR no greater than `1.25` of its trailing one-day median, and no one-ATR M15 shock.
- Signal: a fresh crossing beyond `+/-1.25` rolling 24-bar standard deviations.
- Direction: fade the excursion toward the causal 24-bar midpoint.
- Entry: next contiguous M15 ask for long or bid for short.
- Target: the midpoint frozen at decision time.
- Stop: beyond both `1.25 ATR` from entry and the signal-bar extreme plus a `0.25 ATR` buffer.
- Minimum target distance: `0.50R`.
- Maximum hold: eight M15 bars.
- Maximum entry spread: `0.33R`.
- Same-bar collision: stop first.
- Stress: subtract another `0.10R`.

## Raw And ML Policies

The raw train stream must first have at least 200 trades, baseline PF at least `0.95`, stress PF at least `0.85`, and average stress result at least `-0.05R`.

If it passes, validation compares four frozen policies:

- deterministic specialist with every eligible candidate;
- one fixed model retaining the top 60%, 45%, or 30% by train-score cutoff.

The deterministic policy is judged only on economic gates. ML policies must additionally demonstrate AUC or rank correlation. ML is an optional ranker, not a required source of signals.

## Decision

Failure must be preserved. No threshold, stop, target, policy, feature, model, or gate may change after outcomes are opened. A research survivor would still require exact selected-trade tick replay and prospective shadow evidence before any demo decision.

No EA, demo, live, or broker action is authorized.
