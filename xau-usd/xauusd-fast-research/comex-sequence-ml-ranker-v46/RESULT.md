# COMEX Sequence ML Ranker V46 Result

## Decision

`V46_INTERNAL_EXAM_FAIL_TERMINAL`

The fixed Python ranker is trained and reproducibly locked, but it is not a
tradable model. Historical validation and exam remain sealed. Retraining,
threshold changes, feature changes, alternate seeds, and same-version model
selection are prohibited.

## Model Lock

- Model: shallow `HistGradientBoostingClassifier` registered before fitting.
- Model contract SHA-256:
  `dc2066337e4bc8e72fbca5561ddc7e96af93a8305ea8cc7cff55ed4040e87a6b`.
- Locked probability threshold: `0.2568986845`.
- Threshold calibration: 372 accepted candidates over 129 eligible weekdays,
  or 2.8837/day.
- Calibration active-day share: 96.12%.
- Calibration direction: 183 long and 189 short.
- Threshold labels read: false.
- Internal-exam labels read before model lock: false.

## Internal Exam

- Period: 2024-01-01 through 2024-07-01.
- Eligible full weekdays: 128.
- Accepted resolved trades: 323, or 2.5234/day.
- Direction: 149 long and 174 short.
- Rank AUC: `0.5340`, below the locked `0.55` minimum.
- Base/stress net: `-$193.18/-$218.30`.
- Base/stress PF: `0.5192/0.4785`.
- Mean stress P/L: `-$0.6758/trade`.
- Profitable days: 24.22%; positive months: 0%.
- First/second-half stress PF: `0.3691/0.5815`.
- Top-five-winners-removed stress net: `-$236.35`.
- Closed stress drawdown: `$221.53`, below the `$250` ceiling.
- Bootstrap p-value: `1.0`.

V46 demonstrates that a locked model can preserve the requested satellite
frequency and control closed drawdown, but its ranking information is too weak
and the accepted stream remains strongly negative. It cannot provide Python
predictions, model-training authority for deployment, EA input, demo/live use,
or broker action.
