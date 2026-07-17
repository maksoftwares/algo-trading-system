# A3 ML M5 Cost-Normalized Trend V1 Preregistration

Date: `2026-07-17`

Status: `PREREGISTERED_NOT_IMPLEMENTED_NOT_RUN`

## Premise

The frozen M5 momentum trigger generated `2,842` raw candidates across six years,
about `1.84` per source day, but the old `0.05R` spread-to-stop gate rejected `2,627`
of them. Its 2.5-ATR stop was often too small relative to executable gold spread.

Iteration 8 tests one new premise: a trend continuation event may become economically
usable when its risk and expected movement are deliberately wider than the target
broker's execution cost. This is a new family and version. It does not rewrite or
promote the rejected portability result.

No new profit path has been calculated for the geometries below.

## Frozen Candidate Trigger

V1 reuses the exact source trigger and lane-hour definitions from
`a3_ml_dukascopy_m5_momentum_portability_v1`:

- completed-M5 12-bar breakout and impulse rules;
- causal M5 ATR;
- completed H1 and H4 EMA trend ownership;
- frozen long and short lane thresholds and server-hour masks;
- exact next-quote executable entry within five minutes.

Candidate thresholds and calendar masks may not change in this iteration. The only
new hypothesis is execution geometry.

## Outcome-Blind Geometry Check

Only entry spread, signal ATR, and candidate timestamps were inspected before this
lock. No new-geometry exit or P&L was calculated.

Among `2,807` resolved source entries:

- median executable spread was approximately `$0.33`;
- 95th-percentile spread was approximately `$0.517`;
- a `$7` minimum stop keeps the locked `$0.75` spread floor plus `$0.30` execution
  charge at or below `0.15R` for at least `99.2%` of entries;
- all three frozen stop constructions remain below `$50` initial risk at 0.01 lot for
  at least `99.96%` of observed candidates.

This check sets cost and risk feasibility only. It is not alpha evidence.

## Frozen Geometry Profiles

| Profile | Stop | Target | Timeout |
| --- | --- | --- | --- |
| `CN_TREND_4ATR_1R_12H` | max(4 ATR, $7); reject above $50 | 1.0R | 12 hours |
| `CN_TREND_6ATR_1P5R_24H` | max(6 ATR, $7); reject above $50 | 1.5R | 24 hours |
| `CN_TREND_8ATR_2R_48H` | max(8 ATR, $7); reject above $50 | 2.0R | 48 hours |

Long entries execute at Ask and exit at Bid. Short entries execute at Bid and exit at
Ask. If stop and target are both reachable within one M5 bar, the stop is applied
first. Unresolved and segment-crossing labels are excluded.

Every label subtracts:

- any uplift required to reach a `$0.75` entry-spread floor;
- `$0.30` additional execution cost per 0.01 lot;
- `$0.35` per 24 hours held.

## Windows And Firewall

| Stage | Period |
| --- | --- |
| Development | 2018-07-01 through 2020-06-30 |
| Validation | 2020-07-01 through 2022-06-30 |
| Internal test | 2022-07-01 through 2024-06-30 |
| Exam | 2024-07-01 through 2026-06-30 |

Development selects at most one profile using the frozen gate and ordering. Validation
opens only if a development profile passes. Internal test opens only after validation,
and exam opens only after internal test. The absolute profile does not change between
stages.

This repository has program-level historical contamination, so the exam is not called
an untouched holdout. It is still protected from this V1 geometry until every earlier
stage passes.

## Portfolio And Risk Lock

- fixed 0.01 lot for historical comparability;
- maximum `$50` initial risk per trade;
- maximum two concurrent trades and one per direction;
- maximum `$100` combined initial risk;
- maximum four accepted entries per UTC day;
- maximum immediate cost `0.15R`.

Selected trades must report overlap, direction, source-day frequency, closed drawdown,
month stability, winner concentration, and calendar-month bootstrap uncertainty.

## Acceptance

Development requires at least 300 trades, `0.75` trades per source day, stress PF
`1.10`, average `0.03R`, 55% positive exit months, at least 20% in each direction,
drawdown no greater than `25R`, positive net after removing the ten largest winners,
and a positive 2.5th-percentile calendar-month bootstrap mean.

The PF and average-R requirements rise in each later stage, reaching stress PF `1.25`
and average `0.06R` in exam. Later gates are fully specified in the JSON contract.

## Interpretation Boundary

This is deterministic strategy research. ML ranking is forbidden in V1. If the raw
profile is not positive, no model may rescue it. A complete pass would authorize an
exact target-broker replay and shared-account risk audit, not demo execution.

Python demo prediction, EA consumption, broker action, demo trading, and live capital
remain unauthorized.
