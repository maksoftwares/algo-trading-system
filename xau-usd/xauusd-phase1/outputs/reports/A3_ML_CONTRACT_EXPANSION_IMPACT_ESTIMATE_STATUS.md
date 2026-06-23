# A3 ML Contract Expansion Impact Estimate

Overall status: APPROVAL_ALONE_NOT_SUFFICIENT
Dataset version: xauusd_c02_multiacct_202606220547_geffebb6d_c9221d066

## Summary

- C03 status: NO_GO.
- Candidate files: 13.
- Candidate rows: 2747.
- Candidate estimated groups: 1381.
- Approval alone authorizes demo Python: false.

## Gate Projection

| Gate | Current | Projected | Pass | Why |
| --- | --- | --- | --- | --- |
| dataset_status | PIPELINE_ONLY | PIPELINE_ONLY | false | extra families do not change trainable-label status by themselves |
| market_setup_groups | 223 | 1604 | true | adds C34 estimated out-of-scope groups=1381 |
| minority_labels | 172 | 172 | true | current minority-label gate already reflects approved contract only; C34 has no validated labels |
| active_weeks | 3.37 | 3.37 | false | C34 candidate dates do not extend active decision span enough |
| both_directions | LONG,SHORT | LONG,SHORT | true | current gate already passes; C34 does not reduce coverage |
| at_least_two_regimes | FALLING | FALLING | false | C34 candidates have no proven second-regime C01 feature evidence yet |
| feature_budget | 0 | 0 | false | candidate_trainable_groups=0; extra rows remain non-trainable until label promotion |
| slippage_readiness | INSUFFICIENT | INSUFFICIENT | false | extra signal rows do not create broker fill/request-price coverage for A2/A3 |
| leakage | 0 | 0 | true | leakage must be rechecked after any approved rebuild |

## Result

Approval alone is not enough for demo Python predictions. Remaining projected blockers: dataset_status, active_weeks, at_least_two_regimes, feature_budget, slippage_readiness.

## Required Follow-Up

- If reviewer approves expansion, run C36 with explicit allowed families and review reference, then rerun C08/C07/C03.
- Collect more active market weeks or approved older data that extends the actual decision-date span.
- Promote labels/trainability only through reviewed C02/C01 rules; current rows remain diagnostic/non-trainable.
- Improve A2/A3 broker fill and request-price coverage before official demo Python authorization.
- Collect or approve data that proves at least two non-UNKNOWN regimes in C01.
- Keep broker_action_authorized=false through all rebuilds.

## Boundary

- MT5 connection attempted: false.
- Data export attempted: false.
- Config write attempted: false.
- Model training authorized: false.
- Python demo predictions authorized: false.
- Broker action authorized: false.

## Next

Do not expect reviewer approval alone to authorize demo Python. Continue collecting data and address remaining C03 blockers.
