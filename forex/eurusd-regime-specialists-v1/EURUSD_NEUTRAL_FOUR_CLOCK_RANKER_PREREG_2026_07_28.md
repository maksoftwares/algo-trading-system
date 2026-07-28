# EURUSD Neutral four-clock paired ranker preregistration

Frozen before fitting or inspecting this campaign's historical predictions
and P&L on 2026-07-28.

## Research question

Can direct causal ranking of LONG versus SHORT at four fixed first-hour
clocks approximate the Regime 1 hindsight-oracle trades better than the
previous independent rare-event classifier?

The prior imitation model fit separate `oracle member versus nonmember`
probabilities to every side row, selected a probability threshold on
2021-2022, and then routed at most four accepted rows per date. It did not
fit a paired side label, use a LONG-minus-SHORT feature vector, or force four
fixed choices.

This campaign removes those structural differences without tuning:

- fixed entries at 00:00, 00:15, 00:30, and 00:45 UTC;
- one direction at every clock and no abstention;
- direct paired features equal to the LONG row minus the SHORT row at the
  identical completion timestamp;
- direct training label of LONG winner versus SHORT winner;
- no threshold grid, feature selection, clock selection, or hyperparameter
  search.

## Outcome-blind census

The census command reads only timestamps, sides, and causal feature columns
from the pinned source. It does not read outcomes, target-first labels,
oracle membership, or exit timestamps.

| Window | Eligible Neutral days | Paired decisions / forced trades |
|---|---:|---:|
| 2019-2020 training | 209 | 836 |
| 2021-2022 development holdout | 174 | 696 |
| 2023 validation | 74 | 296 |
| 2024 validation | 66 | 264 |
| 2025 pseudo-OOS | 80 | 320 |
| 2026 H1 pseudo-OOS | 39 | 156 |
| Total | 642 | 2,568 |

All 642 eligible dates have exactly four paired feature rows. Evaluation
therefore contains 1,732 forced trades after the 836-row training period.

## Frozen features

At each clock, each feature is `LONG value - SHORT value`. The 16 fixed
contrasts are:

- EURUSD returns over 1, 3, 6, 12, and 24 completed M5 bars;
- EURUSD EMA gap, anchor gap, close location, and asymmetric room;
- completed-state DXY, EURUSD H1, and Treasury directional gaps;
- completed tick quote-change imbalance over one and three bars;
- completed tick path efficiency and late-bar return.

Non-directional volatility, spread, volume, time-cycle, and weekday features
are excluded because they cancel in a genuine paired direction comparison.
No future path or oracle value is an inference feature.

## Frozen model and chronology

- Standardize features on each training set only.
- L2 logistic regression, `C=0.1`, `liblinear`, balanced classes, and random
  state 20260728.
- Training includes only timestamps where exactly one side reached the
  1.5R target first.
- No-winner timestamps are excluded from model fitting but can never be
  excluded from inference or execution.
- A paired label becomes known only after both side exit timestamps.
- Both entry and paired label-known timestamp must be strictly earlier than
  the inference-window start.
- Refit once at the start of 2021-2022, 2023, 2024, 2025, and 2026 H1.
- Choose LONG at probability at least 0.5 and SHORT otherwise.
- Never abstain and never select a threshold from outcomes.

The 2019-2020 rows are training only. Every later window is inferred from a
model fit exclusively to purged earlier rows.

## Frozen execution

The outcome source was produced by the already locked causal label engine:

- executable bid/ask M5 entry;
- 4-pip stop and 6-pip target;
- 12-hour maximum hold;
- 0.7-pip minimum spread;
- 0.1 pip adverse slippage per execution side;
- stop first when stop and target share one M5 bar.

Overlapping positions are retained. Each of four daily tickets carries 0.25
portfolio R.

## Frozen admission

Every evaluation window must have:

- at least 120 trades;
- 45%-55% win rate;
- realized payoff between 1.35 and 1.75;
- PF at least 1.10 and positive expectancy;
- at least 70% correct direction conditional on one target-first side being
  available;
- daily portfolio PF at least 1.10.

Overall admission also requires:

- ticket PF at least 1.30;
- exact oracle precision at least 40%;
- same-side 15-minute oracle precision at least 45%;
- positive net and PF at least 1.15 after another 0.5 pip per ticket;
- positive net after removing the best 5% of winners;
- daily portfolio drawdown no more than 20R;
- exactly four executed trades on every eligible evaluation date.

## Information status

The archive and earlier model outcomes have already been inspected. This is
adaptive historical research with fixed mechanics and chronological
evaluation, not pristine out-of-sample evidence. Even a complete historical
pass would require at least six post-lock months and 400 new observations
starting 2026-07-29. No historical outcome can authorize broker action.
