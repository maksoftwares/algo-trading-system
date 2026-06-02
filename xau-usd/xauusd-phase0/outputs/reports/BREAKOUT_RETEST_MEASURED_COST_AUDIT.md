# Breakout Retest Measured-Cost Audit

Overall status: FAIL

## Audit Checks

| Audit Check | Status | Evidence |
| --- | --- | --- |
| spread_points unit matches symbol point_size | PASS | point_size is populated before converting spread points to price distance. |
| historical point_size matches broker logger point | REVIEW | Historical conversion uses symbol point_size; passive logger now records point for source rows. |
| measured spread replaces modeled entry spread | PASS | all_in_cost_R subtracts entry_spread_R before adding measured_entry_spread_R. |
| risk_price uses entry/stop price units | PASS | risk_price = abs(entry_price - stop_loss). |
| measured spread R formula | PASS | measured_entry_spread_R = spread_points * point_size / risk_price. |
| slippage and commission are preserved | PASS | Only entry_spread_R is replaced; entry/exit slippage and commission_R remain in all_in_cost_R. |
| stale quote rows excluded from spread model | REVIEW | spread_analysis.py requires tick_fresh and filters to tick_fresh=true before writing cost_model_measured.csv. |
| hour/day/global lookup order | PASS | Measured spread lookup tries hour_utc, then day_of_week_utc, then global fallback. |

## Conclusion

The measured-cost conversion currently blocks breakout-retest paper execution pending human review of the audit evidence.
