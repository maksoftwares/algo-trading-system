# A3 ML Readiness Gap Report

Overall status: GAP_REMAINS
Dataset version: xauusd_c02_multiacct_202606242335_g0a9823b0_c9221d066
C03 status: NO_GO

## Decision Coverage

- Rows: 875
- Min decision UTC: 2026-05-29T09:39:56Z
- Max decision UTC: 2026-06-24T20:29:59Z
- Active span weeks: 3.7788

## Gate Gaps

| Gate | Passed | Observed | Required | Gap |
| --- | --- | --- | --- | --- |
| dataset_status | false | PIPELINE_ONLY | EXPLORATORY_MODEL or higher | needs different category/state |
| market_setup_groups | false | 282 | >=300 | 18 |
| minority_labels | true | 246 | >=90 | 0 |
| active_weeks | false | 3.78 | >=8 | 4.22 weeks |
| both_directions | true | LONG,SHORT | LONG and SHORT | needs different category/state |
| at_least_two_regimes | false | FALLING | >=2 non-UNKNOWN regimes | needs different category/state |
| feature_budget | false | 0 | >=6 | 6 |
| slippage_readiness | false | INSUFFICIENT | ADEQUATE | needs different category/state |
| leakage | true | 0 | 0 | none |

## Slippage Gap

- Overall status: INSUFFICIENT
| Account | Entry | SL | TP | Request | Status |
| --- | --- | --- | --- | --- | --- |
| A1 | 1314 | 787 | 500 | 219 | ADEQUATE |
| A2 | 19 | 12 | 7 | 16 | INSUFFICIENT |
| A3 | 78 | 56 | 22 | 24 | INSUFFICIENT |

## Export Coverage

| Account | Bars | Tick Days | Tick Rows |
| --- | --- | --- | --- |
| A1 | 2026-06-01T00:00:00Z to 2026-06-24T23:35:00Z | 16 | 6367635 |
| A2 | 2026-06-01T00:00:00Z to 2026-06-24T23:35:00Z | 16 | 6367635 |
| A3 | 2026-06-01T00:00:00Z to 2026-06-24T23:35:00Z | 16 | 6367635 |

## Backfill Assessment

- Verdict: NEEDS_MORE_ACTIVE_DECISION_TIME
- Detail: The active-weeks gate is still short; collect more A1/A2/A3 decisions/fills or import older compatible decision logs.
- Estimated earliest C03 active-weeks date: 2026-07-24T09:27:35Z

## Boundary

- MT5 connection attempted: false.
- Data export attempted: false.
- Terminal runtime change authorized: false.
- Model training authorized: false.
- Python demo predictions authorized: false.
- Broker action authorized: false.

## Next Actions

- Keep A1/A2/A3 terminals collecting passive observer data and rerun C10 with --refresh-live-readonly after new market sessions.
- Need about 4.22 more active weeks unless older compatible decisions are imported.
- Need about 18 more market setup groups.
