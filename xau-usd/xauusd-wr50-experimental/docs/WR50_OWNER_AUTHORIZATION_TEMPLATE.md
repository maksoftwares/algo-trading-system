# WR50 Owner Authorization Template

This is a template only. It is not filled, not signed, and not an authorization.

```yaml
owner_name:
authorization_date:
authorization_token:
allowed_account_number:
allowed_server:
allowed_symbol:
allowed_eas:
  - WR50_BreakoutEvening_v0
  - WR50_BreakoutQuality_v0
  - WR50_BreakoutExit1R_v0
max_fixed_lot:
max_daily_loss:
max_total_open_positions:
acknowledgement_not_canonical_phase2: yes/no
acknowledgement_demo_only: yes/no
acknowledgement_no_live_trading: yes/no
acknowledgement_breakout_retest_remains_cost_suspended: yes/no
```

The runtime `InpOwnerAuthorizationToken` must match the filled authorization token used for the demo deployment package. Until filled and reviewed, the registry remains `owner_authorized=false`.

