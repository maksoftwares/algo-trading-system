# A3 ML Macro Regime Event Census V1 Preregistration

Date: 2026-07-16

## Purpose

Price-only Dukascopy research has now rejected M5 momentum portability, M15 range
rotation, M15 range expansion, shock, and the existing microstructure/cross-market ML
ranker. V1 adds materially different causal information: lagged United States real
yields, nominal yields, the yield curve, implied breakeven inflation, and the broad
dollar index.

V1 asks whether four mechanically broad H1 gold events have stable directional
expectancy when macro state agrees with the trade. It is a label census, not a model and
not demo authorization.

## Locked Sources

### Gold execution source

The source is the verified 708,538-row Dukascopy XAUUSD M5 Bid/Ask cache covering
2016-07 through 2026-06. Feature SHA256:
`e587306f530a615dfdc6f869c4f79f881cfa0b572e078fd26d3c9995fbc66228`.

### Target-broker cost source

The accepted broker calibration report has SHA256
`72f4180d518f494dce2f664c6852df0af881edc81b77ab2608d60ec2d86ae7bb`.
V1 locks a $0.75 broker spread floor, another $0.30 per 0.01 lot, maximum total
stressed entry friction of 0.15R, and minimum initial stop distance of $7.00.

### Macro source

Four daily series were downloaded from official Federal Reserve releases through FRED,
from 2016-06-01 through 2026-06-30:

- `DFII10`: 10-year inflation-indexed Treasury yield, H.15;
- `DGS2`: 2-year nominal Treasury yield, H.15;
- `DGS10`: 10-year nominal Treasury yield, H.15;
- `DTWEXBGS`: nominal broad dollar index, H.10.

Every source has 2,630 dated rows and is hash-locked in the JSON contract. Missing
holiday observations remain missing in raw data and are resolved only by causal
backward lookup.

These files are current-vintage historical series, not a complete ALFRED real-time
vintage panel. Corrections to old observations are therefore a disclosed residual
revision risk. V1 makes no untouched-holdout claim.

## Causal Availability

For a gold decision on UTC date D, the newest permitted macro observation date is
D minus two calendar days. The decision may look backward from that eligible date to
the latest nonmissing observation. It may never use same-day or prior-day macro data.

Changes use one, five, and twenty prior valid observations. Long macro alignment
requires both five-observation real-yield change and broad-dollar percentage change to
be nonpositive. Short alignment requires both to be nonnegative.

The frozen macro shock score is:

`-real_yield_change_1 / 0.05 - broad_dollar_pct_change_1 / 0.25`

A score at least +2 supports long; a score at most -2 supports short.

## Frozen Event Families

### Macro-aligned H1 trend pullback

A completed H1 bar must have an aligned 12/48 EMA trend with at least a 0.20ATR gap,
touch and reclaim the fast EMA, have a directional body, and agree with five-observation
real-yield and dollar state. Cooldown is six hours per direction.

### Macro-aligned H1 range break

A completed H1 bar must close at least 0.10ATR outside the prior 24 completed H1 bars,
have at least a 0.50 body fraction, and agree with macro direction. Cooldown is twelve
hours per direction.

### Macro-shock H1 continuation

The frozen macro shock score must support the direction. A completed H1 bar must move
at least 0.50ATR in the same direction and have at least a 0.45 body fraction. Cooldown
is twelve hours per direction.

### Macro-divergence H1 reclaim

Price must make at least a 0.10ATR excursion beyond the prior 24-hour range against
the aligned macro direction and close back inside that range with a directional body.
The trade follows macro direction. Cooldown is twelve hours per direction.

Only family plus direction can promote: four families times long and short, eight
hypotheses total. No session, month, volatility, score, or context subgroup may promote.

## Frozen Execution

The signal is known only at the completed H1 close. Entry is the next contiguous M5
bar at executable Ask for long and Bid for short. Stops use the family-specific maximum
of completed-bar structure, fixed H1 ATR distance, and $7.00. Initial 0.01-lot risk may
not exceed $50.

Targets are fixed at 1.5R or 2.0R by family. Maximum holds are fixed from 36 to 72
hours. Long paths use Bid and short paths use Ask. Stop gaps fill at the worse executable
open and same-M5 stop/target collisions are stop-first.

Stress uses native Dukascopy spread but floors entry friction at $0.75, adds $0.30 per
0.01 lot, and adds $0.35 per 24 hours. Total stressed entry friction above 0.15R is
ineligible.

These are conservative M5 screens. Every survivor requires exact-tick replay.

## Chronological Firewall

- train: 2016-07-01 through 2020-06-30;
- validation: 2020-07-01 through 2022-06-30;
- internal test: 2022-07-01 through 2024-06-30;
- exam: 2024-07-01 through 2026-06-30;
- prospective holdout begins 2026-07-01.

Train must pass before validation opens; validation must pass before internal test
opens; internal test must pass before exam opens. A recent result cannot rescue an
earlier failure.

## Gates

Train requires at least 100 events, stress PF at least 1.10, average at least +0.03R,
at least 50% positive active exit months, drawdown no more than 30R, positive net after
removing the ten largest winners, and calendar-month bootstrap mean-R 2.5th percentile
above zero.

Validation, internal test, and exam require at least 40 events with progressively
stronger PF, average R, month stability, drawdown, and winner-removal gates. Exam also
requires at least 0.05 events per source day.

## Decision Rule

- source or label-quality failure: `MACRO_REGIME_EVENT_CENSUS_INVALID`;
- no train survivor: close all V1 policies;
- later chronological failure: close that identical family-direction policy;
- all gates pass: authorize only a new exact-tick specialist hypothesis;
- no ML model is trained unless a sufficiently large positive label population survives;
- no parameter, subgroup, model, or threshold search is authorized in V1.

## Authorization

- research only: yes;
- specialist hypothesis only after every gate: yes;
- model training: no;
- Python demo predictions: no;
- EA consumption: no;
- broker action: no.
