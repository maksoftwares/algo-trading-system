# V60 ML Sizing Causal Retest V1 Preregistration

Locked before any corrected feature matrix or corrected model result was
calculated.

## Question

Does the other agent's fixed V4 model still improve the current deterministic
V60 portfolio after:

1. using only M5 bars that were complete before each trade entry;
2. matching the currently executable nine-source population;
3. applying the deployed V57 same-direction 120-minute post-loss cooldown;
4. measuring full floating-equity drawdown rather than only closed P&L;
5. accounting for time dependence; and
6. translating the sizing rule into broker-expressible 0.01-lot increments?

## Frozen Inputs

- V60 fee-stressed price ledger, SHA-256
  `ba9044e0f5ef73292b3b243c39c6b9aa8d7f9921da33633b3354281f378b5bbf`.
- Dukascopy M5 feature cache, SHA-256
  `e587306f530a615dfdc6f869c4f79f881cfa0b572e078fd26d3c9995fbc66228`.
- Current V60 demo configuration, SHA-256
  `053bbb0e0d0f8e365f8b93b8a7d61376c6762c861ad1ec2c1b3d796d3089a9df`.
- Source commit `d03e0c35fb57835d6e6d6e68648abb45032d2ebb`.

R5 is excluded because it is not in the deployed source list. The V57 cooldown
is replayed causally using only previously accepted trades that had closed
before the next entry.

## Feature Availability

The M5 cache timestamp is the bar-open timestamp. A row is eligible only when:

```text
bar_open_timestamp + 5 minutes <= trade_entry_timestamp
```

The last eligible row is used. All market windows end on that row. The primary
model uses the original 16 market features plus `is_long` and `is_core`.
Portfolio-state features remain excluded because the original ablation found no
incremental value.

## Frozen Model

- Annual expanding walk-forward, test years 2021 through 2026.
- Train only on trades with `exit_time < test_year_start - 48 hours`.
- Target: fee-stressed USD P&L winsorized at the training 1st and 99th
  percentiles.
- `HistGradientBoostingRegressor`:
  `max_depth=3`, `max_iter=200`, `learning_rate=0.05`,
  `min_samples_leaf=40`, `l2_regularization=1.0`, `random_state=0`.
- Forty bootstrap bags.
- Primary ensemble seed: `0`. Seeds 1 through 4 are sensitivity diagnostics and
  cannot replace seed 0.
- Causal expanding out-of-sample rank mapping. Use prior out-of-sample scores
  after 150 observations; before that, use the training prediction
  distribution.
- Multiplier band `[0.5, 1.5]`, training-size shrinkage
  `min(1, sqrt(n_train / 1500))`, and constant normalizer `1.0`.

No model parameter, feature, threshold, seed, or gate may change after the
corrected result is observed.

## Policies

### Continuous research policy

Keep every eligible trade and multiply its complete P&L and mark-to-market path
by the causal multiplier. This measures whether the ranking contains useful
allocation information, but it is not broker executable at a 0.01 base lot.

### Broker-expressible policy

The fixed outcome-blind translation is:

- multiplier below `0.75`: `0.00` lots;
- multiplier from `0.75` through `1.25`: `0.01` lots;
- multiplier above `1.25`: `0.02` lots only when the trade's known scaled
  initial risk and the historical concurrent-risk path remain within the
  current V60 source and account limits; otherwise `0.01` lots;
- missing initial risk never permits `0.02` lots.

This policy is deliberately evaluated separately because it changes frequency
and is not equivalent to the continuous research policy.

## Historical Pass Gates

All gates must pass. A partial pass remains research-only.

1. Every selected market row is available no later than entry.
2. Corrected continuous net P&L is at least the same-trade baseline.
3. Corrected continuous full floating drawdown is no worse than baseline and
   net/floating-DD improves by at least 5%.
4. Green-month share is no more than two percentage points below baseline.
5. At least five of six entry years have nonnegative P&L improvement.
6. A weekly-block bootstrap of the P&L delta has a 95% lower bound above zero.
7. Improvement after subtracting naive mean-multiplier leverage remains
   positive.
8. The broker-expressible policy independently passes gates 2 through 6.
9. The broker-expressible path respects every source, account, directional,
   concurrent-position, and floating-drawdown limit.

The old row-wise permutation p-value is diagnostic only. It cannot authorize
deployment because trades overlap and the architecture was selected after
observing this historical record.

## Demo Decision

Even a historical pass does not authorize a runtime change. It permits creation
of a deterministic, fail-closed demo-shadow candidate and a new prospective
contract. Broker-affecting demo sizing requires a separate explicit deployment
approval after the candidate passes current-account preflight.

Any failed gate means the current deterministic V60 demo remains unchanged.
