# A3 ML Dukascopy Event Census V1 Preregistration

Date: 2026-07-16

## Purpose

Iteration 4 stops guessing fully specified strategies and asks a narrower empirical
question: which broad, causal XAUUSD events have stable directional expectancy after
executable spread and fixed stress costs?

This census is frozen before event labels or outcomes are generated. A passing result
may authorize a new specialist hypothesis and preregistration. It cannot authorize
demo or live execution.

## Locked Source

The census reuses the Iteration 3 M5 cache derived from the verified Dukascopy Bid/Ask
foundation:

- period: 2016-07 through 2026-06;
- M5 rows: 708,538;
- source digest:
  `4282fffda04d3b23218d4064b67e036af15b9b2937df3f0fb434d68bfb6ae738`;
- feature SHA256:
  `e587306f530a615dfdc6f869c4f79f881cfa0b572e078fd26d3c9995fbc66228`;
- source report SHA256:
  `689763a8654c429f112c3322bc68cf3a1c678a7d55b904354deeca3297847cb3`.

The run must fail closed if the path, hash, row count, or source digest differs.

## Frozen Event Populations

### Trend pullback resumption

A completed M5 decision must have an aligned 12/48 EMA trend with a minimum 0.25ATR
gap, a same-direction 60-minute return of at least 0.75ATR, and a completed-bar touch
and reclaim of the fast EMA. Events have a 30-minute per-direction cooldown.

### Session opening drive

At the end of the first six M5 bars of London or New York, the completed opening move
must be at least 0.75ATR, have directional efficiency of at least 0.55, and have mean
quote intensity at least normal. There is one event per declared session and UTC date.

### Session range break

The first completed M5 close on each side outside the completed Asia or London range
must exceed the boundary by 0.05ATR, have at least a 0.35 body fraction, and have
aligned tick imbalance. The reference requires at least 60 active M5 bars.

### Volatility expansion break

The prior 12 completed M5 bars must span no more than 2.5ATR while ATR ratio is no
greater than 1.0. The completed decision bar must close at least 0.05ATR beyond that
range with body fraction at least 0.35 and quote intensity at least 0.8. Events have a
60-minute per-direction cooldown.

All exact numerical rules are in `config/ml/a3_ml_dukascopy_event_census_v1.json`.

## Causal Labels

The event decision is the end of its completed M5 bar. Entry is the next contiguous
M5 bar's first executable quote:

- long entry at Ask and long marking/exits at Bid;
- short entry at Bid and short marking/exits at Ask;
- entry spread must be no more than 0.15ATR;
- maximum initial 0.01-lot barrier risk is $50.

Every event receives directional return, MFE, and MAE labels at 30, 60, 120, and 240
minutes. It also receives three fixed 1.5 reward/risk barrier labels:

- 0.50ATR stop / 0.75ATR target / 120-minute timeout;
- 0.75ATR stop / 1.125ATR target / 240-minute timeout;
- 1.00ATR stop / 1.50ATR target / 240-minute timeout.

Same-bar stop/target collisions are stop-first. Native spread is present in executable
quotes. Stress subtracts another $0.30 per event plus $0.35 per 24 hours held.

These are bar-screen labels, not final fill evidence. Any survivor requires exact tick
replay under a new specialist preregistration.

## Context Labels

Each event is tagged with its declared profile, UTC session, volatility bin, and trend
alignment. Those fields are diagnostic-only in V1. They cannot be used to select or
promote a subgroup after outcomes are seen.

Only eight family-plus-direction hypotheses are eligible: four families times long and
short. This prevents a large context grid from manufacturing an apparent edge.

## Chronological Firewall

- train: 2016-07-01 through 2020-06-30;
- validation: 2020-07-01 through 2022-06-30;
- internal test: 2022-07-01 through 2024-06-30;
- exam: 2024-07-01 through 2026-06-30;
- prospective holdout begins 2026-07-01.

For each family-direction hypothesis, train may select exactly one of the three barrier
profiles using the locked gate and tie-break order. The identical selected profile is
then carried forward without change. Validation must pass before internal test opens;
internal test must pass before exam opens.

The historical program has inspected parts of all retrospective periods, so V1 does
not claim an untouched holdout.

## Gates

Train requires at least 200 events, stress PF at least 1.10, average stress result at
least 0.02R, at least 50% positive active exit months, closed drawdown at most 35R,
positive net after removing the ten largest winners, and a calendar-month bootstrap
2.5th percentile for mean stress R above zero.

Validation and internal test require at least 80 events and progressively stronger PF,
average R, stability, drawdown, and winner-removal gates. Exam requires at least 80
events, at least 0.12 events per source day, PF at least 1.25, average result at least
0.04R, at least 55% positive active months, drawdown at most 20R, and positive net
after removing the five largest winners.

All gates must pass in order. A recent positive result cannot rescue a failed train or
validation population.

## Decision Rule

- no train survivor: close the event family-direction hypothesis;
- train pass but later failure: close the identical policy;
- all gates pass: authorize only a new specialist hypothesis and preregistration;
- no parameter, context, horizon, or barrier tuning is permitted after V1 outcomes;
- no ML model is trained unless a sufficiently large, economically positive label
  population survives the chronological firewall.

## Authorization

The census is research-only. It cannot publish Python demo predictions, feed an EA,
or place broker orders.
