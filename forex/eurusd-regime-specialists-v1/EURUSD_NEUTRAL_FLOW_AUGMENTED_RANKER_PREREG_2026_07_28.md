# EURUSD Neutral flow-augmented paired-ranker preregistration

Frozen before the first outcome-bearing run of this combined model on
2026-07-28.

## Research question

The standalone sign of executed EURUSDT taker flow was not predictive, but
the source can still add information conditionally. Does a strict linear
ranker combining executed flow with the already frozen EURUSD side contrasts
select the winning side of each Regime 1 pair out of sample?

This is the only planned fitted use of the downloaded Binance source. It is
not a search over flow horizons, strengths, transformations, interactions,
models, thresholds, clocks, or subgroups.

## Outcome-blind census and chronology

The census reads timestamps and completed decision-time features but does
not read EURUSD outcomes, target-first labels, oracle membership, or exit
timestamps.

| Window | Role | Eligible Neutral dates | Forced decisions |
|---|---|---:|---:|
| 2020-2021 | training only | 185 | 740 |
| 2022-2023 | validation | 149 | 596 |
| 2024 | validation | 66 | 264 |
| 2025 | pseudo-OOS | 80 | 320 |
| 2026 H1 | pseudo-OOS | 39 | 156 |
| Total | | 519 | 2,076 |

The 2020-2021 points are never scored. Evaluation contains 1,336 forced
trades on 334 complete Neutral dates, exactly four per retained date.

At each evaluation-window start, the model may train on earlier
one-winner pairs only when both the entry and the maximum of the LONG and
SHORT exit timestamps are strictly earlier than that start. All no-winner
points remain mandatory at inference.

## Frozen features

The first 16 columns are the unchanged LONG-minus-SHORT contrasts from the
four-clock ranker:

- EURUSD returns over 1, 3, 6, 12, and 24 completed M5 bars;
- EURUSD EMA gap, anchor gap, close location, and asymmetric room;
- completed-state DXY, EURUSD H1, and Treasury directional gaps;
- completed tick quote-change imbalance over one and three bars;
- completed tick path efficiency and late-bar return.

Exactly two Binance variables are appended:

- taker-buy quote imbalance across the prior three consecutive, fully
  completed EURUSDT M5 bars;
- EURUSDT return across those same three completed bars.

Volume, trade count, nonlinear interactions, and strength thresholds are
excluded. They are not added after seeing this result.

## Frozen model, execution, and admission

- Standardize on each purged training set only.
- L2 logistic regression with `C=0.1`, `liblinear`, balanced classes, random
  state 20260728.
- Fixed probability threshold 0.5; LONG on a tie.
- No feature selection, hyperparameter search, calibration, sign reversal,
  or abstention.
- Fixed entries at 00:00, 00:15, 00:30, and 00:45 UTC.
- Executable EURUSD bid/ask labels with 4-pip stop, 6-pip target, 12-hour
  maximum hold, 0.7-pip minimum spread, 0.1-pip adverse slippage per side,
  and stop-first same-bar handling.
- Each of the four overlapping tickets carries 0.25 portfolio R.

Every evaluation window must have at least 120 trades, 45%-55% win rate,
1.35-1.75 realized payoff, PF at least 1.10, positive expectancy, at least
70% conditional side accuracy, daily PF at least 1.10, and exactly four
trades per eligible date.

Overall gates remain PF 1.30, exact oracle precision 40%, same-side
15-minute precision 45%, stressed PF 1.15 with positive net, positive net
after removing the best 5% of winners, and daily portfolio drawdown no more
than 20R.

## Evidence status

This is adaptive historical research because earlier EURUSD campaigns and
the standalone flow result have already been inspected. A historical pass
cannot authorize broker action. Promotion would still require at least 400
untouched observations and six calendar months after the 2026-07-29 lock.
