# A3 ML Power And MDE Protocol V1

Status: PRELOCK_CONTRACT

This contract owns paired delta, block bootstrap, confidence intervals, power, and minimum detectable effect.

## Paired Comparison Unit

For every raw base signal:

```text
model_portfolio_R =
  model_take * y_net_R_p95_stress

rule_portfolio_R =
  rule_take * y_net_R_p95_stress

delta_R =
  model_portfolio_R - rule_portfolio_R
```

Skipped signals contribute zero.

This prevents a low-frequency model from appearing superior only because metrics are calculated on a small retained subset.

## Bootstrap

Use:

- active trading day as base block;
- 5-active-day moving block bootstrap;
- 10,000 replicates;
- weekly-block sensitivity.

Do not bootstrap individual trades independently.

## Confidence Intervals

Report 90 percent and 95 percent intervals for:

- PF;
- expectancy;
- win rate;
- retention;
- drawdown;
- incremental delta_R.

Final gates use one-sided 95 percent lower bounds where specified by the model-selection contract.

## Minimum Detectable Effect

Estimate sample required for:

- +0.03R per retained-trade improvement;
- +0.05R per retained-trade improvement;
- +0.10R per retained-trade improvement;
- positive delta_R per raw base signal.

Use:

- two-sided alpha = 0.05;
- power = 0.80;
- empirical block variance.

If evidence is underpowered, status is CONTINUE_EVIDENCE.

Do not force PASS or FAIL from underpowered evidence.
