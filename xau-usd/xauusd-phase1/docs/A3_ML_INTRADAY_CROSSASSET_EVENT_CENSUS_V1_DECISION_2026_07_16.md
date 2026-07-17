# A3 ML Intraday Cross-Asset Event Census V1 Decision

Date: 2026-07-16

Classification: `INTRADAY_CROSSASSET_NO_TRAIN_SURVIVOR`

## Pipeline Result

All source, causality, chronology, uniqueness, broker-cost, label-completion,
and joined-coverage gates passed.

- M15 feature rows: 177,136
- Joined intraday source days: 1,909 of 2,332 XAU active days, or 81.8611%
- Outcome-blind events: 17,277
- Train labels opened: 6,921
- Resolved train labels: 6,733
- Ineligible train labels: 188
- Train source days: 743
- Validation, internal test, and exam outcomes opened: none

## Train Evidence

| Family | Direction | Events | Events/day | Stress PF | Average R | Net R | Closed DD R | Positive months |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Bond impulse continuation | Long | 1,140 | 1.5343 | 0.6957 | -0.1538 | -175.352 | 181.378 | 19.4% |
| Bond impulse continuation | Short | 1,126 | 1.5155 | 0.6643 | -0.1819 | -204.832 | 214.023 | 19.4% |
| Cross-asset agreement continuation | Long | 952 | 1.2813 | 0.7262 | -0.1356 | -129.111 | 140.855 | 27.8% |
| Cross-asset agreement continuation | Short | 957 | 1.2880 | 0.7175 | -0.1491 | -142.716 | 148.605 | 30.6% |
| Cross-asset lead/gold catch-up | Long | 97 | 0.1306 | 0.5127 | -0.2833 | -27.476 | 28.668 | 25.7% |
| Cross-asset lead/gold catch-up | Short | 86 | 0.1157 | 0.4537 | -0.3222 | -27.705 | 30.322 | 27.6% |
| Dollar impulse continuation | Long | 1,211 | 1.6299 | 0.6920 | -0.1587 | -192.210 | 201.186 | 19.4% |
| Dollar impulse continuation | Short | 1,164 | 1.5666 | 0.6769 | -0.1756 | -204.402 | 204.726 | 13.9% |

Every hypothesis failed PF, average-R, month-stability, bootstrap, and
winner-removal robustness gates. Most also exceeded the drawdown limit. The
lead/catch-up family additionally failed minimum event count.

## Interpretation

The intraday source was useful for creating many causal candidate labels, so
data scarcity and raw frequency were not the blockers in this iteration. The
fixed continuation and catch-up mechanisms had materially negative expectancy
after realistic Bid/Ask execution and target-broker stress in train. More trades
made the loss estimate more certain; they did not create an edge.

The 6,733 resolved labels exceed the count prerequisite for downstream ML, but
there are no final specialist survivors and no long/short survivor pair.
Training a selector on these labels would optimize a rejected mechanism and is
not authorized.

## Decision

Reject the four fixed cross-asset families. Do not loosen their thresholds,
change their stops or targets, reverse them, inspect later outcomes, or train a
model on them within this iteration. A future iteration must preregister a
materially different mechanism before outcomes are opened.

No Python demo prediction, EA consumption, broker action, or live trading is
authorized.
