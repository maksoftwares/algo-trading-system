# Experimental Demo Daily Review Template

Overall status: TEMPLATE_NOT_AUTHORIZATION

Use this template only if the owner separately authorizes the quarantined experimental demo lane. This review does not contribute to canonical Phase 2 readiness.

## Daily Review Fields

```text
review_date_utc:
reviewer:
account_login:
server:
authorized_candidates_checked:
kill_switch_file_checked:
order_log_files_reviewed:
open_positions_start:
open_positions_end:
new_orders_sent:
new_orders_blocked_by_guard:
cost_R_guard_blocks:
spread_guard_blocks:
manual_interventions:
unexpected_behavior:
stop_condition_triggered:
end_of_day_reconciliation_complete:
review_decision: CONTINUE / PAUSE / STOP
```

## Required Checks

- Confirm server is demo, not live/real.
- Confirm account login matches the owner authorization.
- Confirm every order row has candidate, symbol, magic, spread, estimated cost_R, SL, TP, and order mode.
- Confirm no same-family demo fill is treated as Phase 2 evidence.
- Confirm open demo orders/positions are reconciled before the next session.

## Boundary

Daily review can only support experimental guard design. It cannot override measured-cost failure or cost suspension.
