# Causal Macro Action Models V6 Preregistration

## Purpose

V6 tests one narrow hypothesis: completed dollar-index and US Treasury total-return
state may improve the already locked Adaptive V5 action rankers. It does not search
for new candidate events, actions, labels, model classes, thresholds, regimes, or
execution rules.

All history through 2026-06-30 is exposed development data. Passing this experiment
would justify further forward research only. It would not authorize ML shadowing,
demo trading, live trading, Python serving, EA consumption, sizing, or broker action.

## Locked Comparator And Population

- Comparator: Adaptive V5, with exact input and result hashes in the configuration.
- Population: the corrected Expanded Dataset V4 action rows and six purged folds.
- Lanes: downside impulse retest, opening range reversal, and break and run, with
  the same disjoint priority as V5.
- Labels, structural weights, stress costs, fixed-action baselines, and unsafe-shock
  exclusions are unchanged.
- The same ridge model, four training-window variants, three retention quantiles,
  calibration-only selection, and UTC-week bootstrap are retained.

## Macro Source

Only the verified free Dukascopy `DOLLARIDXUSD` and `USTBONDTRUSD` M5 cache is
authorized. Its file and manifest SHA-256 values, row count, and time boundary are
locked in configuration. No Databento, paid source, silver, EURUSD, GBPUSD, USDJPY,
or post-June-2024 broad cross-asset cache is used.

Three complete M5 rows form an M15 bar. Its timestamp is the bar completion time.
At each candidate decision, V6 may use only the latest completed M15 macro row at or
before the signal time, with maximum age 10 minutes. No nearest or forward join is
allowed.

## Locked Feature Change

The 58 Adaptive V5 features are augmented with exactly eight values:

1. Direction-adjusted DXY-implied gold pressure over 15m, 1h, and 4h.
2. Direction-adjusted Treasury total-return gold pressure over 15m, 1h, and 4h.
3. Direction-adjusted one-hour DXY/Treasury consensus.
4. Absolute one-hour DXY/Treasury disagreement.

Each pressure is a completed return divided by a scale computed from prior returns;
the rolling scale is shifted one bar. Missing macro values are median-imputed only by
the model pipeline fitted inside each training partition. No missingness indicator is
added, no global imputation is allowed, and no event is removed for macro absence.

## Selection And Acceptance

For each lane and fold, the four locked Adaptive V5 training variants are fitted on
the 66-feature surface. The retention policy is selected only on that fold's
calibration partition. Test outcomes do not choose a variant or threshold.

All Adaptive V5 absolute acceptance gates remain unchanged, including:

- all six calibration folds pass;
- positive selected mean and profit factor after stress;
- lower confidence bounds for selected mean and action uplift;
- drawdown no worse than the fixed-action baseline;
- at least four positive folds and weighted AUC at least 0.53;
- nonnegative F2026 mean, F2026 PF at least 1.05, and nonnegative F2026 action
  uplift;
- frequency at least 0.5 selected candidate events per weekday.

V6 must also not regress against Adaptive V5 in aggregate selected mean R, aggregate
profit factor, or F2026 mean R, and must retain at least 90% of V5 candidate-event
frequency. These are development gates, not proof of future edge.

## Interpretation

- A fail means these eight macro features do not justify promotion under this fixed
  formulation.
- A pass is a research lead only because all test eras are already exposed.
- Candidate-event frequency is not executable account trade frequency or P&L.
- No same-version tuning is allowed after outcomes are opened.
