# A3 ML Readiness Gap Report

Overall status: WAITING_FOR_DECISION_HISTORY
Dataset version: xauusd_c02_multiacct_202606220547_geffebb6d_c9221d066
C03 status: NO_GO

## Decision Coverage

- Rows: 574
- Min decision UTC: 2026-05-29T09:39:56Z
- Max decision UTC: 2026-06-22T00:19:58Z
- Active span weeks: 3.373

## Gate Gaps

| Gate | Passed | Observed | Required | Gap |
| --- | --- | --- | --- | --- |
| dataset_status | false | PIPELINE_ONLY | EXPLORATORY_MODEL or higher | needs different category/state |
| market_setup_groups | false | 223 | >=300 | 77 |
| minority_labels | true | 172 | >=90 | 0 |
| active_weeks | false | 3.37 | >=8 | 4.63 weeks |
| both_directions | true | LONG,SHORT | LONG and SHORT | needs different category/state |
| at_least_two_regimes | false | FALLING | >=2 non-UNKNOWN regimes | needs different category/state |
| feature_budget | false | 0 | >=6 | 6 |
| slippage_readiness | false | INSUFFICIENT | ADEQUATE | needs different category/state |
| leakage | true | 0 | 0 | none |

## Slippage Gap

- Overall status: INSUFFICIENT
| Account | Entry | SL | TP | Request | Status |
| --- | --- | --- | --- | --- | --- |
| A1 | 1307 | 783 | 497 | 215 | ADEQUATE |
| A2 | 12 | 8 | 4 | 12 | INSUFFICIENT |
| A3 | 75 | 54 | 21 | 24 | INSUFFICIENT |

## Export Coverage

| Account | Bars | Tick Days | Tick Rows |
| --- | --- | --- | --- |
| A1 | 2026-02-22T23:00:00Z to 2026-06-22T05:45:00Z | 13 | 4906823 |
| A2 | 2026-02-22T23:00:00Z to 2026-06-22T05:45:00Z | 13 | 4906823 |
| A3 | 2026-02-22T23:00:00Z to 2026-06-22T05:45:00Z | 13 | 4906823 |

## Backfill Assessment

- Verdict: OLDER_MARKET_HISTORY_EXISTS_BUT_NO_OLDER_USABLE_DECISIONS
- Detail: MT5 market history begins before the first labeled decision, so bars/ticks alone are not enough; older EA decision logs or more live observer time are needed.
- Estimated earliest C03 active-weeks date: 2026-07-24T10:10:22Z

## Boundary

- MT5 connection attempted: false.
- Data export attempted: false.
- Terminal runtime change authorized: false.
- Model training authorized: false.
- Python demo predictions authorized: false.
- Broker action authorized: false.

## Next Actions

- Import older compatible EA decision/observer logs if available; market bars/ticks alone cannot satisfy active decision weeks.
- Keep A1/A2/A3 terminals collecting passive observer data and rerun C10 with --refresh-live-readonly after new market sessions.
- Need about 4.63 more active weeks unless older compatible decisions are imported.
- Need about 77 more market setup groups.
