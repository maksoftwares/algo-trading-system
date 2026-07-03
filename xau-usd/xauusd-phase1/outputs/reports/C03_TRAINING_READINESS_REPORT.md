# C03 Training Readiness Report

Overall status: NO_GO

## Authorization

- Training authorized: false
- Python demo predictions authorized: false
- EA consumption authorized: false
- Broker action authorized: false

## Gates

| Gate | Passed | Observed | Required |
| --- | --- | --- | --- |
| dataset_status | false | PIPELINE_ONLY | EXPLORATORY_MODEL or higher |
| market_setup_groups | true | 323 | >=300 |
| minority_labels | true | 302 | >=90 |
| active_weeks | false | 4.07 | >=8 |
| both_directions | true | LONG,SHORT | LONG and SHORT |
| at_least_two_regimes | false | FALLING | >=2 non-UNKNOWN regimes |
| feature_budget | false | 0 | >=6 |
| slippage_readiness | false | INSUFFICIENT | ADEQUATE |
| leakage | true | 0 | 0 |

## Next

continue evidence collection and rerun C02/C03 after more signals/fills
