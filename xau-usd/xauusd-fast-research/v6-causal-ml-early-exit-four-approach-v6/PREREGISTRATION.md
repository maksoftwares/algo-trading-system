# V6 Causal ML Early Exit Four-Approach Preregistration

## Purpose

V4 and V5 often identified avoidable losses, but a small number of recoveries
made early exits economically harmful. This campaign locks and tests four
different model structures without searching thresholds after outcomes.

## Frozen Foundation

- Frozen V1 selected nominations and broad causal corpus.
- Frozen V3 checkpoints at 30, 60, 120, and 240 minutes.
- Frozen V5 XAUUSD and cross-asset feature block.
- Frozen stressed benefit target:
  `(early stressed P&L - original stressed P&L) / initial risk`.
- Frozen annual target years 2022-2026, 48-hour outcome purge, decision-day
  weights, action guards, costs, routing, windows, and account limits.
- No model sees a source trade whose original exit falls inside the purge
  boundary for its target year.

## Arm A: Competing Utility

Fit three shallow histogram gradient-boosting models:

- probability that exiting now has positive stressed benefit;
- 25th-percentile benefit magnitude among beneficial exits;
- 75th-percentile sacrifice magnitude among harmful exits.

Score:

`P(benefit) * benefit_q25 - (1 - P(benefit)) * sacrifice_q75`

The frozen adverse-state guards apply, and the score must be at least 0.00R.

## Arm B: Entry-Regime Competing Utility

Fit the same three models separately for each entry regime:
`R0_SHOCK`, `R1_UPTREND`, `R2_DOWNTREND`, `R3_COMPRESSION`, `R4_CHOP`, and
`R5_TRANSITION`.

Entry regime is known before entry. Later specialist names are not used because
the broad training corpus does not contain a consistent specialist identity.
Each annual regime model requires at least 5,000 total rows and 1,000 rows in
each magnitude subset. The same score and action guards as Arm A apply.

## Arm C: Causal Path Sequence

Add 48 ordered M5 signed-return positions and 48 activity masks to the frozen
V5 matrix. At decision time `T`, the newest sequence bar is timestamped
`T - 5 minutes`; no bar opening at or after `T` is allowed. Positions before
trade entry are zero with mask zero.

Fit the frozen-style 25th-percentile histogram gradient-boosting regressor to
the unclipped stressed benefit target. Exit when its lower-benefit score is at
least 0.00R and every frozen adverse-state guard passes.

## Arm D: Unanimous Ensemble

No fourth model is fitted. Exit only when Arms A, B, and C all trigger at the
same causal checkpoint. Its comparison score is the minimum of the three arm
scores.

## Models

All fitted models use:

- learning rate 0.05;
- 150 iterations;
- at most 15 leaves and depth 3;
- minimum leaf size 250;
- L2 regularization 2.0;
- no early stopping;
- fixed random state 260727;
- equal total weight per UTC decision day.

No clipping, calibration, feature search, threshold search, or neighboring
configuration is authorized.

## Pass Conditions

Each arm is judged independently against the frozen V5 gates:

- mean annual Spearman at least 0.05 and at least three positive years;
- positive first-action net benefit in at least three years;
- at least 70% beneficial first actions and positive total benefit;
- early exits between 1% and 20% of frozen V1 nominations;
- no reduction in V1 net or PF and no increase in V1 closed drawdown in any
  required window or full history;
- no worsening of shared-account net, PF, closed drawdown, or floating
  drawdown;
- all inherited exposure and source-coverage limits pass.

## Governance

All inspected history is development evidence. A failed arm is quarantined.
A passing arm remains research-only and requires a separately locked
prospective period and MT5 parity. The best-looking failed arm cannot be
selected for execution, and this campaign cannot be tuned in place.
