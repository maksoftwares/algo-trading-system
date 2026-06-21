# A3 ML Data Contract V1

Status: PRELOCK_CONTRACT

Scope: A3 account 1033669, XAUUSD only, breakout_retest only.

This contract owns the source universe, row schema, feature-time ordering, trainable-label rules, data audit schema, and per-fold class-count schema.

## Source Universe

Use every unique raw breakout-retest would-signal, not only executed trades.

Include:

- executed signals;
- blocked signals;
- session-blocked signals;
- cost-blocked signals;
- trend-blocked signals;
- duplicate-lane signals;
- future shadow signals.

Allowed source classes:

- raw observer decisions;
- M5, M15, H1, H4, and D1 bars;
- ticks;
- measured spreads;
- actual broker fills;
- position paths;
- virtual-trade events;
- session and time metadata.

Actual broker history is used only to validate reconstruction, build empirical slippage, and audit execution realism.

## Prohibited Decision-Time Inputs

Never use as model inputs:

- future bar or future tick;
- final PnL;
- MFE or MAE;
- exit reason;
- future spread;
- future slippage;
- post-signal balance;
- post-signal daily PnL;
- manual outcome label;
- later model score.

The recent reviewed three-week period is discovery/development data. It is not a final holdout.

## Required Row Times

Each row contains:

- feature_time_utc;
- decision_time_utc;
- entry_eligible_from_utc;
- label_end_time_utc.

Required ordering:

```text
feature_time_utc <= decision_time_utc
decision_time_utc < entry_eligible_from_utc
entry_eligible_from_utc <= label_end_time_utc
```

All bars used by features must be completed before decision_time_utc.

Any violation is DATA_LEAKAGE_FAIL and stops the build.

## Trainable Labels

Trainable rows exclude:

- CANCELLED_NO_FRESH_TICK;
- DATA_UNRESOLVED_TIMEOUT;
- EXECUTION_AMBIGUITY;
- DATA_UNRESOLVED.

Supervised fitting uses y_win_expected as the primary classification target.

Final trading gates use y_net_R_p95_stress.

## Audit Schema

A3_ML_DATA_AUDIT.md and machine-readable data audits must report:

- raw source row counts;
- exact signal counts;
- fuzzy setup-group counts;
- labeled and trainable setup groups;
- class balance;
- direction balance;
- regime balance;
- event-duration distribution;
- missingness;
- unresolved label counts;
- duplicate and fuzzy-duplicate rates;
- slippage adequacy status;
- dataset status: PIPELINE_ONLY, EXPLORATORY_MODEL, CANDIDATE_MODEL, or MATURE_MODEL.

## Per-Fold Class-Count Schema

The feature-budget contract owns the exact per-fold purge, embargo, calibration, model-fit class-count, minority-event, and binding-fold diagnostic schema.

Data audits must include that schema by reference and must not maintain a second copy of the field list in this contract.

## Inventory Horizon Sensitivity

During inventory only, report mechanics for:

- 96 active M5 bars;
- 144 active M5 bars;
- 288 active M5 bars primary.

Allowed mechanics:

- resolved label count;
- unresolved label count;
- median event duration;
- P95 event duration;
- purge loss by fold;
- post-calibration minority count;
- implied feature budget.

Prohibited outcome metrics:

- PF;
- expectancy;
- win rate;
- model score;
- threshold.

The 288-bar horizon remains primary unless a new versioned label contract is created for trade-economic reasons under the execution-label contract governance.
