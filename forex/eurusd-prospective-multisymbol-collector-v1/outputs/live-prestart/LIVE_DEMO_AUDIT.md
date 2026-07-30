# EURUSD prospective collector live-demo audit

Status: `PASS_RUNNING_PRESTART`

- Audited at UTC: `2026.07.30 06:14:50`
- Demo identity: `1033669 / Capital.ComMena-Demo`
- Terminal build: `5833`
- Feature rows: `0`
- Heartbeat rows: `6`
- Latest heartbeat UTC: `2026.07.30 06:14:45`
- Heartbeat age seconds: `5.0`

## Checks

- [x] `environment_present`
- [x] `heartbeat_present`
- [x] `scope_is_prospective_demo`
- [x] `account_is_demo`
- [x] `trade_permission_is_none`
- [x] `chart_is_eurusd_m5`
- [x] `source_list_exact`
- [x] `forward_floor_exact`
- [x] `startup_latch_present`
- [x] `no_feature_rows_before_floor`
- [x] `prestart_transition_refused`
- [x] `heartbeat_fresh`

A pre-start pass proves only that the read-only collector is running safely. It does not prove a trading edge.
