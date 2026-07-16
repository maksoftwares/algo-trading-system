# A3 ML Dukascopy Confirmed Event Specialists V1 Preregistration

Date: 2026-07-16

## Purpose

Iteration 3 tests three short-hold XAUUSD event mechanisms that are structurally
different from the rejected generic breakout, sweep, range-fade, and immediate-shock
families. The goal is to find independently useful opportunity coverage that fits a
0.01-lot demo account risk floor. It does not loosen or retune R1 or R2.

This preregistration is frozen before generating or inspecting V1 outcomes.

## Prior Evidence And Exclusions

The following frozen results are source-locked in the JSON contract:

- daily compression breakout: 31 trades, stress PF 0.948, invalid;
- eight simple London/New York breakout and sweep profiles: no train survivor;
- generic M5 trend, range, and shock families: no train survivor;
- prior MT5 compression and chop campaigns: no confirmed specialist.

V1 must not recreate those families with cosmetic naming changes. In particular, it
does not enter on an unconfirmed boundary break, a raw range z-score, or the first bar
of a shock.

## Frozen Families

### Session boundary sweep and reclaim

The completed M5 bar must sweep a completed Asia or London session boundary, close
back inside by a fixed ATR margin, leave a material rejection wick, and have aligned
5-minute and 15-minute tick imbalance. London versus Asia and New York versus London
are declared profiles of one family, not separately selectable parameter variants.

### Compression break and retest

A 12-bar compressed range must exist before the breakout. The breakout requires a
large body, directional efficiency, and normal-or-better quote intensity. Entry is
permitted only after a later completed bar retests and holds the broken boundary with
aligned tick imbalance.

### Shock failure and reclaim

A three-bar displacement must meet fixed ATR, efficiency, and quote-intensity gates.
The strategy then waits for a separate completed bar to retrace at least half of that
move and confirm reversal with tick imbalance. It never enters on the impulse bar.

All numerical definitions are locked in
`config/ml/a3_ml_dukascopy_confirmed_event_specialists_v1.json`.

## Causality And Execution

- Every decision uses only completed M5 bars and ticks timestamped before the decision.
- Entry is the first executable Dukascopy tick at or after the decision, within five
  minutes.
- Longs enter at Ask and exit at Bid. Shorts enter at Bid and exit at Ask.
- Stops and targets are evaluated in chronological tick order.
- Native spread is included. Stress subtracts another $0.30 per trade plus $0.35 per
  24 hours held.
- Initial 0.01-lot stop risk cannot exceed $50 on the nominal $10,000 demo account.
- Entry spread cannot exceed 0.15R.
- Each mechanism has a short, fixed timeout between three and six hours.

The existing verified 120-month Dukascopy foundation, acquisition manifests, and
source hashes are authoritative. MT5 generated ticks are not used as labels.

## Chronological Firewall

The frozen windows are:

- train: 2016-07-01 through 2020-06-30;
- validation: 2020-07-01 through 2022-06-30;
- internal test: 2022-07-01 through 2024-06-30;
- exam: 2024-07-01 through 2026-06-30;
- prospective holdout begins 2026-07-01.

A family must pass train and validation before its internal-test outcome is eligible
for a promotion decision. It must then pass internal test before its exam outcome is
eligible. The implementation may calculate all labels in one replay for efficiency,
but classification must preserve this firewall and must not use later outcomes to
choose a family.

The historical program has already inspected portions of every retrospective window.
Therefore V1 explicitly does not claim an untouched holdout. A retrospective survivor
can become only a forward-shadow candidate until prospective evidence is collected.

## Acceptance Logic

The exact family and portfolio gates are locked in the JSON contract. Important exam
requirements include:

- all 120 source months valid, unique chronological candidates, and at least 99%
  resolved executable labels;
- at least 60 trades and 15 in each direction per surviving family;
- at least 0.12 trades per source day per surviving family;
- stress PF at least 1.30 and average stress R at least 0.05;
- at least 55% positive active exit months;
- closed drawdown no greater than 15R;
- positive net after removing the five largest winners.

The combined survivor portfolio must deliver at least 0.35 trades per source day in
the exam, stress PF at least 1.30, average stress R at least 0.05, closed drawdown at
most 20R, no more than 35% of positive net from one overlap episode, and positive net
after removing the three best episodes.

Passing these gates is evidence of a research survivor, not demo authorization.

## Anti-Overfit Decision Rule

There is no parameter grid in V1. After outcomes are generated:

- a family that fails train is rejected without opening later periods for promotion;
- a family that passes train but fails validation is rejected;
- a family that reaches and fails internal test or exam is rejected;
- thresholds are not changed and V1 is not rerun;
- any redesigned mechanism requires a new version and a new preregistration.

If no family survives, the correct Iteration 3 result is no survivor. Frequency must
not be manufactured by lowering quality gates.

## Authorization Boundary

V1 is research-only. It cannot send predictions to an EA, authorize demo trading, or
place broker orders. A survivor must next pass exact shared-account risk composition,
implementation parity, and prospective shadow checks.
